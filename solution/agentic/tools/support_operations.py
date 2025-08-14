"""
Support Operation Tools with Database Abstraction

This module implements functional tools for support operations that abstract
interaction with the CultPass database and provide structured responses.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import re
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, and_, or_
import uuid

# Import database models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'models'))
from cultpass import User, Experience, Subscription, Reservation
from udahub import Account, Ticket, TicketMessage

class OperationStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"

@dataclass
class OperationResult:
    """Structured result for support operations"""
    status: OperationStatus
    data: Dict[str, Any]
    message: str
    operation_id: str
    timestamp: datetime
    metadata: Dict[str, Any]

class DatabaseAbstraction:
    """Abstracts database interactions for support operations"""
    
    def __init__(self, cultpass_db_path: str, udahub_db_path: str):
        self.cultpass_engine = create_engine(f"sqlite:///{cultpass_db_path}")
        self.udahub_engine = create_engine(f"sqlite:///{udahub_db_path}")
    
    def get_cultpass_session(self) -> Session:
        """Get CultPass database session"""
        return Session(self.cultpass_engine)
    
    def get_udahub_session(self) -> Session:
        """Get Uda-hub database session"""
        return Session(self.udahub_engine)
    
    def execute_with_session(self, db_type: str, operation: callable) -> Any:
        """Execute operation with proper session management"""
        if db_type == "cultpass":
            session = self.get_cultpass_session()
        else:
            session = self.get_udahub_session()
        
        try:
            result = operation(session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

class SupportOperationTools:
    """
    Support operation tools with database abstraction for
    account lookup, subscription management, and refund processing.
    """
    
    def __init__(self, cultpass_db_path: str, udahub_db_path: str):
        self.db = DatabaseAbstraction(cultpass_db_path, udahub_db_path)
        self.operation_log = []
    
    def _log_operation(self, operation_type: str, result: OperationResult):
        """Log operation for audit trail"""
        log_entry = {
            "operation_type": operation_type,
            "operation_id": result.operation_id,
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "message": result.message
        }
        self.operation_log.append(log_entry)
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID"""
        return f"op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_user_id(self, user_id: str) -> bool:
        """Validate user ID format"""
        return user_id and len(user_id) > 0
    
    def account_lookup(self, identifier: str, identifier_type: str = "email") -> OperationResult:
        """
        Look up account information by email or user ID
        
        Args:
            identifier: Email address or user ID
            identifier_type: "email" or "user_id"
            
        Returns:
            OperationResult with account information
        """
        operation_id = self._generate_operation_id()
        
        try:
            # Validate input
            if identifier_type == "email" and not self._validate_email(identifier):
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message="Invalid email format",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"identifier": identifier, "identifier_type": identifier_type}
                )
            
            if identifier_type == "user_id" and not self._validate_user_id(identifier):
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message="Invalid user ID format",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"identifier": identifier, "identifier_type": identifier_type}
                )
            
            # Perform database lookup
            def lookup_operation(session: Session):
                if identifier_type == "email":
                    user = session.query(User).filter(User.email == identifier).first()
                else:
                    user = session.query(User).filter(User.user_id == identifier).first()
                
                if not user:
                    return None
                
                # Get related data
                subscriptions = session.query(Subscription).filter(Subscription.user_id == user.user_id).all()
                reservations = session.query(Reservation).filter(Reservation.user_id == user.user_id).all()
                
                return {
                    "user": user,
                    "subscriptions": subscriptions,
                    "reservations": reservations
                }
            
            result_data = self.db.execute_with_session("cultpass", lookup_operation)
            
            if not result_data:
                return OperationResult(
                    status=OperationStatus.NOT_FOUND,
                    data={},
                    message=f"Account not found for {identifier_type}: {identifier}",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"identifier": identifier, "identifier_type": identifier_type}
                )
            
            # Format response data
            user_data = {
                "user_id": result_data["user"].user_id,
                "full_name": result_data["user"].full_name,
                "email": result_data["user"].email,
                "is_blocked": result_data["user"].is_blocked,
                "subscription_count": len(result_data["subscriptions"]),
                "reservation_count": len(result_data["reservations"]),
                "active_subscriptions": [
                    {
                        "subscription_id": sub.subscription_id,
                        "plan_type": sub.plan_type,
                        "status": sub.status,
                        "start_date": sub.start_date.isoformat() if sub.start_date else None,
                        "end_date": sub.end_date.isoformat() if sub.end_date else None
                    }
                    for sub in result_data["subscriptions"]
                ],
                "recent_reservations": [
                    {
                        "reservation_id": res.reservation_id,
                        "experience_id": res.experience_id,
                        "reservation_date": res.reservation_date.isoformat() if res.reservation_date else None,
                        "status": res.status
                    }
                    for res in result_data["reservations"][:5]  # Last 5 reservations
                ]
            }
            
            result = OperationResult(
                status=OperationStatus.SUCCESS,
                data=user_data,
                message=f"Account found successfully for {identifier_type}: {identifier}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"identifier": identifier, "identifier_type": identifier_type}
            )
            
            self._log_operation("account_lookup", result)
            return result
            
        except Exception as e:
            result = OperationResult(
                status=OperationStatus.ERROR,
                data={},
                message=f"Error during account lookup: {str(e)}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"identifier": identifier, "identifier_type": identifier_type}
            )
            self._log_operation("account_lookup", result)
            return result
    
    def subscription_management(self, user_id: str, action: str, **kwargs) -> OperationResult:
        """
        Manage user subscriptions (create, update, cancel, renew)
        
        Args:
            user_id: User ID
            action: "create", "update", "cancel", "renew", "status"
            **kwargs: Additional parameters based on action
            
        Returns:
            OperationResult with subscription information
        """
        operation_id = self._generate_operation_id()
        
        try:
            # Validate input
            if not self._validate_user_id(user_id):
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message="Invalid user ID format",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "action": action}
                )
            
            if action not in ["create", "update", "cancel", "renew", "status"]:
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message=f"Invalid action: {action}",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "action": action}
                )
            
            # Perform subscription operation
            def subscription_operation(session: Session):
                if action == "create":
                    return self._create_subscription(session, user_id, **kwargs)
                elif action == "update":
                    return self._update_subscription(session, user_id, **kwargs)
                elif action == "cancel":
                    return self._cancel_subscription(session, user_id, **kwargs)
                elif action == "renew":
                    return self._renew_subscription(session, user_id, **kwargs)
                elif action == "status":
                    return self._get_subscription_status(session, user_id)
            
            result_data = self.db.execute_with_session("cultpass", subscription_operation)
            
            if not result_data:
                return OperationResult(
                    status=OperationStatus.NOT_FOUND,
                    data={},
                    message=f"User not found or no subscription data for user: {user_id}",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "action": action}
                )
            
            result = OperationResult(
                status=OperationStatus.SUCCESS,
                data=result_data,
                message=f"Subscription {action} completed successfully for user: {user_id}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"user_id": user_id, "action": action}
            )
            
            self._log_operation("subscription_management", result)
            return result
            
        except Exception as e:
            result = OperationResult(
                status=OperationStatus.ERROR,
                data={},
                message=f"Error during subscription {action}: {str(e)}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"user_id": user_id, "action": action}
            )
            self._log_operation("subscription_management", result)
            return result
    
    def _create_subscription(self, session: Session, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create new subscription"""
        tier = kwargs.get("plan_type", "basic")  # Map plan_type to tier
        duration_months = kwargs.get("duration_months", 1)
        
        subscription = Subscription(
            subscription_id=str(uuid.uuid4()),
            user_id=user_id,
            tier=tier,
            status="active",
            monthly_quota=4,  # Default quota
            started_at=datetime.now(),
            ended_at=datetime.now() + timedelta(days=30 * duration_months)
        )
        
        session.add(subscription)
        session.flush()
        
        return {
            "subscription_id": subscription.subscription_id,
            "plan_type": subscription.tier,  # Map tier back to plan_type for consistency
            "status": subscription.status,
            "start_date": subscription.started_at.isoformat(),
            "end_date": subscription.ended_at.isoformat() if subscription.ended_at else None,
            "action": "created"
        }
    
    def _update_subscription(self, session: Session, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update existing subscription"""
        subscription_id = kwargs.get("subscription_id")
        if not subscription_id:
            raise ValueError("subscription_id is required for update")
        
        subscription = session.query(Subscription).filter(
            and_(Subscription.subscription_id == subscription_id, Subscription.user_id == user_id)
        ).first()
        
        if not subscription:
            return None
        
        # Update fields
        if "plan_type" in kwargs:
            subscription.tier = kwargs["plan_type"]  # Map plan_type to tier
        if "status" in kwargs:
            subscription.status = kwargs["status"]
        if "end_date" in kwargs:
            subscription.ended_at = kwargs["end_date"]
        
        return {
            "subscription_id": subscription.subscription_id,
            "plan_type": subscription.tier,  # Map tier back to plan_type
            "status": subscription.status,
            "start_date": subscription.started_at.isoformat(),
            "end_date": subscription.ended_at.isoformat() if subscription.ended_at else None,
            "action": "updated"
        }
    
    def _cancel_subscription(self, session: Session, user_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel subscription"""
        subscription_id = kwargs.get("subscription_id")
        if not subscription_id:
            raise ValueError("subscription_id is required for cancellation")
        
        subscription = session.query(Subscription).filter(
            and_(Subscription.subscription_id == subscription_id, Subscription.user_id == user_id)
        ).first()
        
        if not subscription:
            return None
        
        subscription.status = "cancelled"
        subscription.ended_at = datetime.now()
        
        return {
            "subscription_id": subscription.subscription_id,
            "plan_type": subscription.tier,  # Map tier back to plan_type
            "status": subscription.status,
            "start_date": subscription.started_at.isoformat(),
            "end_date": subscription.ended_at.isoformat(),
            "action": "cancelled"
        }
    
    def _renew_subscription(self, session: Session, user_id: str, **kwargs) -> Dict[str, Any]:
        """Renew subscription"""
        subscription_id = kwargs.get("subscription_id")
        duration_months = kwargs.get("duration_months", 1)
        
        if not subscription_id:
            raise ValueError("subscription_id is required for renewal")
        
        subscription = session.query(Subscription).filter(
            and_(Subscription.subscription_id == subscription_id, Subscription.user_id == user_id)
        ).first()
        
        if not subscription:
            return None
        
        subscription.status = "active"
        subscription.ended_at = datetime.now() + timedelta(days=30 * duration_months)
        
        return {
            "subscription_id": subscription.subscription_id,
            "plan_type": subscription.tier,  # Map tier back to plan_type
            "status": subscription.status,
            "start_date": subscription.started_at.isoformat(),
            "end_date": subscription.ended_at.isoformat(),
            "action": "renewed"
        }
    
    def _get_subscription_status(self, session: Session, user_id: str) -> Dict[str, Any]:
        """Get subscription status"""
        subscriptions = session.query(Subscription).filter(Subscription.user_id == user_id).all()
        
        return {
            "user_id": user_id,
            "subscription_count": len(subscriptions),
            "active_subscriptions": [
                {
                    "subscription_id": sub.subscription_id,
                    "plan_type": sub.tier,  # Map tier to plan_type
                    "status": sub.status,
                    "start_date": sub.started_at.isoformat() if sub.started_at else None,
                    "end_date": sub.ended_at.isoformat() if sub.ended_at else None
                }
                for sub in subscriptions
            ]
        }
    
    def refund_processing(self, user_id: str, reservation_id: str, reason: str, amount: float = None) -> OperationResult:
        """
        Process refund for a reservation
        
        Args:
            user_id: User ID
            reservation_id: Reservation ID
            reason: Refund reason
            amount: Refund amount (optional, defaults to full amount)
            
        Returns:
            OperationResult with refund information
        """
        operation_id = self._generate_operation_id()
        
        try:
            # Validate input
            if not self._validate_user_id(user_id):
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message="Invalid user ID format",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "reservation_id": reservation_id}
                )
            
            if not reservation_id:
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message="Reservation ID is required",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "reservation_id": reservation_id}
                )
            
            # Process refund
            def refund_operation(session: Session):
                # Find reservation
                reservation = session.query(Reservation).filter(
                    and_(Reservation.reservation_id == reservation_id, Reservation.user_id == user_id)
                ).first()
                
                if not reservation:
                    return None
                
                # Check if reservation is eligible for refund
                if reservation.status not in ["confirmed", "paid"]:
                    return {"error": "Reservation not eligible for refund"}
                
                # Calculate refund amount
                refund_amount = amount if amount is not None else 100.0  # Default amount
                
                # Update reservation status
                reservation.status = "refunded"
                # Note: The Reservation model doesn't have refund fields, so we'll just update status
                # In a real implementation, you'd have a separate Refund table
                
                # Create refund record (simplified)
                refund_data = {
                    "refund_id": str(uuid.uuid4()),
                    "reservation_id": reservation_id,
                    "user_id": user_id,
                    "amount": refund_amount,
                    "reason": reason,
                    "status": "processed",
                    "processed_date": datetime.now().isoformat()
                }
                
                return {
                    "refund_id": refund_data["refund_id"],
                    "reservation_id": reservation_id,
                    "user_id": user_id,
                    "amount": refund_amount,
                    "reason": reason,
                    "status": "processed",
                    "reservation_status": reservation.status
                }
            
            result_data = self.db.execute_with_session("cultpass", refund_operation)
            
            if not result_data:
                return OperationResult(
                    status=OperationStatus.NOT_FOUND,
                    data={},
                    message=f"Reservation not found or not eligible for refund: {reservation_id}",
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "reservation_id": reservation_id}
                )
            
            if "error" in result_data:
                return OperationResult(
                    status=OperationStatus.VALIDATION_ERROR,
                    data={},
                    message=result_data["error"],
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    metadata={"user_id": user_id, "reservation_id": reservation_id}
                )
            
            result = OperationResult(
                status=OperationStatus.SUCCESS,
                data=result_data,
                message=f"Refund processed successfully for reservation: {reservation_id}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"user_id": user_id, "reservation_id": reservation_id, "reason": reason}
            )
            
            self._log_operation("refund_processing", result)
            return result
            
        except Exception as e:
            result = OperationResult(
                status=OperationStatus.ERROR,
                data={},
                message=f"Error during refund processing: {str(e)}",
                operation_id=operation_id,
                timestamp=datetime.now(),
                metadata={"user_id": user_id, "reservation_id": reservation_id}
            )
            self._log_operation("refund_processing", result)
            return result
    
    def get_operation_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get operation log for audit trail"""
        return self.operation_log[-limit:] if limit else self.operation_log
    
    def clear_operation_log(self):
        """Clear operation log"""
        self.operation_log.clear()
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get tool status and statistics"""
        return {
            "tool_name": "SupportOperationTools",
            "available_operations": [
                "account_lookup",
                "subscription_management", 
                "refund_processing"
            ],
            "total_operations_logged": len(self.operation_log),
            "database_connections": {
                "cultpass": str(self.db.cultpass_engine.url),
                "udahub": str(self.db.udahub_engine.url)
            },
            "status": "operational"
        }
