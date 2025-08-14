#!/usr/bin/env python3
"""
Database Setup Verification Script

This script verifies that the database setup meets all requirements from the specification:
- Database infrastructure is set up
- Required tables exist
- Knowledge base has 14+ articles
- Articles cover diverse categories
- All operations complete without errors
- Data retrieval works successfully
"""

import os
import json
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_database_files_exist():
    """Test that database files are created"""
    print("🔍 Testing database file existence...")
    
    cultpass_db = "data/external/cultpass.db"
    udahub_db = "data/core/udahub.db"
    
    if not os.path.exists(cultpass_db):
        print(f"❌ CultPass database not found: {cultpass_db}")
        return False
    
    if not os.path.exists(udahub_db):
        print(f"❌ Uda-hub database not found: {udahub_db}")
        return False
    
    print("✅ Database files exist")
    return True

def test_required_tables():
    """Test that all required tables exist in Uda-hub database"""
    print("\n🔍 Testing required tables...")
    
    udahub_db = "data/core/udahub.db"
    engine = create_engine(f"sqlite:///{udahub_db}")
    
    required_tables = ['accounts', 'users', 'tickets', 'ticket_metadata', 'ticket_messages', 'knowledge']
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        existing_tables = [row[0] for row in result]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            return False
        
        print("✅ All required tables present")
        return True

def test_knowledge_base_articles():
    """Test that knowledge base has at least 14 articles"""
    print("\n🔍 Testing knowledge base articles...")
    
    # Test JSONL file
    articles_file = "data/external/cultpass_articles.jsonl"
    if not os.path.exists(articles_file):
        print(f"❌ Articles file not found: {articles_file}")
        return False
    
    articles = []
    with open(articles_file, 'r', encoding='utf-8') as f:
        for line in f:
            articles.append(json.loads(line))
    
    if len(articles) < 14:
        print(f"❌ Expected at least 14 articles, but found only {len(articles)}")
        return False
    
    print(f"✅ Found {len(articles)} articles in JSONL file")
    
    # Test database
    udahub_db = "data/core/udahub.db"
    engine = create_engine(f"sqlite:///{udahub_db}")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM knowledge"))
        db_count = result.scalar()
        
        if db_count < 14:
            print(f"❌ Expected at least 14 articles in database, but found only {db_count}")
            return False
        
        print(f"✅ Found {db_count} articles in database")
    
    return True

def test_article_categories():
    """Test that articles cover diverse categories"""
    print("\n🔍 Testing article categories...")
    
    articles_file = "data/external/cultpass_articles.jsonl"
    articles = []
    
    with open(articles_file, 'r', encoding='utf-8') as f:
        for line in f:
            articles.append(json.loads(line))
    
    categories = set()
    for article in articles:
        tags = article.get('tags', '').split(', ')
        categories.update(tags)
    
    print(f"📋 Found categories: {sorted(categories)}")
    print(f"📊 Total categories: {len(categories)}")
    
    # Check for diverse categories (at least 5 different categories)
    if len(categories) < 5:
        print(f"❌ Expected at least 5 categories, but found only {len(categories)}")
        return False
    
    print("✅ Articles cover diverse categories")
    return True

def test_data_retrieval():
    """Test that data can be successfully retrieved from databases"""
    print("\n🔍 Testing data retrieval...")
    
    # Test CultPass database
    cultpass_db = "data/external/cultpass.db"
    engine_cultpass = create_engine(f"sqlite:///{cultpass_db}")
    
    with engine_cultpass.connect() as conn:
        # Test experiences
        result = conn.execute(text("SELECT COUNT(*) FROM experiences"))
        exp_count = result.scalar()
        print(f"🎭 CultPass experiences: {exp_count}")
        
        # Test users
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"👥 CultPass users: {user_count}")
    
    # Test Uda-hub database
    udahub_db = "data/core/udahub.db"
    engine_udahub = create_engine(f"sqlite:///{udahub_db}")
    
    with engine_udahub.connect() as conn:
        # Test accounts
        result = conn.execute(text("SELECT COUNT(*) FROM accounts"))
        account_count = result.scalar()
        print(f"🏢 Uda-hub accounts: {account_count}")
        
        # Test knowledge base
        result = conn.execute(text("SELECT COUNT(*) FROM knowledge"))
        kb_count = result.scalar()
        print(f"📚 Knowledge base articles: {kb_count}")
        
        # Test sample data retrieval
        result = conn.execute(text("SELECT title FROM knowledge LIMIT 1"))
        sample = result.fetchone()
        if sample:
            print(f"📖 Sample article: {sample[0]}")
    
    print("✅ Data retrieval successful")
    return True

def test_database_operations():
    """Test that database operations complete without errors"""
    print("\n🔍 Testing database operations...")
    
    try:
        # Test basic operations
        udahub_db = "data/core/udahub.db"
        engine = create_engine(f"sqlite:///{udahub_db}")
        
        with engine.connect() as conn:
            # Test simple queries
            conn.execute(text("SELECT 1"))
            conn.execute(text("SELECT COUNT(*) FROM knowledge"))
            conn.execute(text("SELECT COUNT(*) FROM accounts"))
            
        print("✅ Database operations complete without errors")
        return True
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 DATABASE SETUP VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("Database Files Exist", test_database_files_exist),
        ("Required Tables", test_required_tables),
        ("Knowledge Base Articles", test_knowledge_base_articles),
        ("Article Categories", test_article_categories),
        ("Data Retrieval", test_data_retrieval),
        ("Database Operations", test_database_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ SPECIFICATION REQUIREMENTS MET:")
        print("  ✓ Database infrastructure set up")
        print("  ✓ Required tables created")
        print("  ✓ Knowledge base populated with 14+ articles")
        print("  ✓ Articles cover diverse categories")
        print("  ✓ All operations completed without errors")
        print("  ✓ Data retrieval demonstrated")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the failed tests above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
