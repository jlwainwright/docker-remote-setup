#!/usr/bin/env python3
"""
Database setup script for CyberZapend
This script will:
1. Create all database tables
2. Populate properties from config.yaml
3. Create users and meters from the data files
4. Import historical vending transactions
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Property, User, Meter, VendingTransaction

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL for synchronous connection"""
    sqlite_url = "sqlite:///./cyberzapvend.db"
    database_url = os.environ.get("DATABASE_URL", sqlite_url)
    # Convert async URL to sync URL for setup
    if "aiosqlite" in database_url:
        database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
    return database_url

def create_database_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    
    # Get database URL
    database_url = get_database_url()
    logger.info(f"Using database: {database_url}")
    
    engine = create_engine(database_url, echo=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    return engine

def parse_datetime(dt_str):
    """Parse datetime string to timezone-aware datetime"""
    if not dt_str or dt_str == 'null':
        return None
    
    try:
        # Handle various datetime formats
        if 'T' in dt_str:
            if dt_str.endswith('Z'):
                # UTC format
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            elif '+' in dt_str or dt_str.count('-') > 2:
                # Already has timezone
                return datetime.fromisoformat(dt_str)
            else:
                # Naive datetime, assume UTC
                dt = datetime.fromisoformat(dt_str)
                return dt.replace(tzinfo=timezone.utc)
        else:
            # Date only
            dt = datetime.fromisoformat(dt_str)
            return dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.warning(f"Could not parse datetime '{dt_str}': {e}")
        return None

def populate_properties(session, config_data):
    """Populate properties from config.yaml"""
    logger.info("Populating properties...")
    
    for config_key, prop_details in config_data.items():
        logger.info(f"Processing property: {config_key}")
        
        # Determine pricing model
        tariffs = prop_details.get('tariffs', {})
        pricing_model = 'flat'
        if 'tier1_rate' in tariffs and 'tier2_rate' in tariffs:
            pricing_model = 'tiered'
        
        # Check if property already exists
        existing_property = session.execute(
            select(Property).filter_by(config_key=config_key)
        ).scalar_one_or_none()
        
        if existing_property:
            logger.info(f"Property {config_key} already exists, updating...")
            property_obj = existing_property
        else:
            property_obj = Property(config_key=config_key)
            session.add(property_obj)
        
        # Set property attributes
        property_obj.name = prop_details.get('name', config_key)
        property_obj.pricing_model = pricing_model
        property_obj.tier1_rate = Decimal(str(tariffs.get('tier1_rate', 0))) if tariffs.get('tier1_rate') else None
        property_obj.tier2_rate = Decimal(str(tariffs.get('tier2_rate', 0))) if tariffs.get('tier2_rate') else None
        property_obj.tier1_limit_kwh = Decimal(str(tariffs.get('tier1_limit', 0))) if tariffs.get('tier1_limit') else None
        property_obj.flat_rate_kwh = Decimal(str(tariffs.get('flat_rate', 0))) if tariffs.get('flat_rate') else None
        property_obj.vat_rate = Decimal(str(tariffs.get('vat_rate', 0.15)))
        property_obj.vending_fee = Decimal(str(prop_details.get('vending_fee', 0)))
        property_obj.receipt_dir_template = prop_details.get('paths', {}).get('receipt_dir')
        
        session.flush()  # Get the ID
        logger.info(f"Property {property_obj.name} processed successfully")
    
    session.commit()
    logger.info("Properties populated successfully")

def populate_users_and_meters(session, config_data):
    """Populate users, meters, and transactions from data files"""
    logger.info("Populating users, meters, and transactions...")
    
    for prop_config_key, prop_details in config_data.items():
        # Get the property
        property_obj = session.execute(
            select(Property).filter_by(config_key=prop_config_key)
        ).scalar_one_or_none()
        
        if not property_obj:
            logger.error(f"Property {prop_config_key} not found, skipping")
            continue
        
        # Get data file path
        data_file = prop_details.get('paths', {}).get('data_file')
        if not data_file:
            logger.warning(f"No data file specified for property {prop_config_key}")
            continue
        
        data_file_path = project_root / data_file
        if not data_file_path.exists():
            logger.warning(f"Data file not found: {data_file_path}")
            continue
        
        # Load user data
        try:
            with open(data_file_path, 'r') as f:
                users_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading data file {data_file_path}: {e}")
            continue
        
        # Process each user
        for user_data in users_data:
            meter_number = user_data.get('meter_number')
            user_name = user_data.get('name', f"User {meter_number}")
            
            if not meter_number:
                logger.warning(f"No meter number for user {user_name}, skipping")
                continue
            
            logger.info(f"Processing meter {meter_number} for user {user_name}")
            
            # Create or get user
            placeholder_google_id = f"{meter_number}@placeholder.google.com"
            placeholder_email = f"{meter_number}@placeholder.email.com"
            
            user_obj = session.execute(
                select(User).filter_by(google_id=placeholder_google_id)
            ).scalar_one_or_none()
            
            if not user_obj:
                user_obj = User(
                    google_id=placeholder_google_id,
                    email=placeholder_email,
                    name=user_name,
                    role='Tenant',
                    is_active=True
                )
                session.add(user_obj)
                session.flush()
                logger.info(f"Created user {user_name}")
            else:
                logger.info(f"User {user_name} already exists")
            
            # Create or get meter
            meter_obj = session.execute(
                select(Meter).filter_by(meter_number=meter_number)
            ).scalar_one_or_none()
            
            if not meter_obj:
                meter_obj = Meter(
                    meter_number=meter_number,
                    property_id=property_obj.id,
                    assigned_user_id=user_obj.id,
                    meter_type='ELECTRICITY',
                    status='Active',
                    config_user_name_hint=user_name
                )
                session.add(meter_obj)
                session.flush()
                logger.info(f"Created meter {meter_number}")
            else:
                # Update existing meter
                meter_obj.property_id = property_obj.id
                meter_obj.assigned_user_id = user_obj.id
                meter_obj.config_user_name_hint = user_name
                logger.info(f"Updated meter {meter_number}")
            
            # Process vending transactions
            vend_count = 0
            for vend_data in user_data.get('vends', []):
                transaction_date = parse_datetime(vend_data.get('date'))
                amount = vend_data.get('amount')
                kwh = vend_data.get('kwh')
                
                if not transaction_date or amount is None:
                    logger.warning(f"Invalid vend data for meter {meter_number}: {vend_data}")
                    continue
                
                # Check if transaction already exists
                existing_transaction = session.execute(
                    select(VendingTransaction).filter_by(
                        meter_id=meter_obj.id,
                        transaction_date=transaction_date,
                        amount_paid_currency=Decimal(str(amount))
                    )
                ).scalar_one_or_none()
                
                if existing_transaction:
                    continue  # Skip existing transactions
                
                # Create tariff snapshot
                tariff_snapshot = {
                    'source_tier1_kwh': vend_data.get('tier1_kwh'),
                    'source_tier2_kwh': vend_data.get('tier2_kwh'),
                    'property_tier1_rate': str(property_obj.tier1_rate) if property_obj.tier1_rate else None,
                    'property_tier2_rate': str(property_obj.tier2_rate) if property_obj.tier2_rate else None,
                    'property_tier1_limit_kwh': str(property_obj.tier1_limit_kwh) if property_obj.tier1_limit_kwh else None,
                    'property_flat_rate_kwh': str(property_obj.flat_rate_kwh) if property_obj.flat_rate_kwh else None,
                    'property_vat_rate': str(property_obj.vat_rate),
                    'property_vending_fee': str(property_obj.vending_fee)
                }
                
                transaction = VendingTransaction(
                    meter_id=meter_obj.id,
                    initiated_by_user_id=user_obj.id,
                    transaction_date=transaction_date,
                    amount_paid_currency=Decimal(str(amount)),
                    kwh_vended=Decimal(str(kwh)) if kwh is not None else Decimal('0'),
                    token_from_vendor=vend_data.get('token'),
                    tariff_details_snapshot=tariff_snapshot,
                    raw_vend_data_from_cli=vend_data
                )
                session.add(transaction)
                vend_count += 1
            
            logger.info(f"Added {vend_count} transactions for meter {meter_number}")
            
            # Update meter's last token info
            if user_data.get('last_token_number'):
                meter_obj.last_token_number_in_month = user_data['last_token_number']
            
            if user_data.get('last_token_month'):
                last_token_date = parse_datetime(user_data['last_token_month'])
                if last_token_date:
                    meter_obj.last_token_sequence_month = last_token_date.date()
        
        session.commit()
        logger.info(f"Completed processing property {prop_config_key}")
    
    logger.info("Users, meters, and transactions populated successfully")

def create_admin_user(session):
    """Create default admin user"""
    logger.info("Creating admin user...")
    
    admin_user = session.execute(
        select(User).filter_by(google_id="admin@zapvend.local")
    ).scalar_one_or_none()
    
    if not admin_user:
        admin_user = User(
            google_id="admin@zapvend.local",
            email="admin@zapvend.local",
            name="Admin User",
            role="Admin",
            is_active=True
        )
        session.add(admin_user)
        session.commit()
        logger.info("Admin user created successfully")
    else:
        logger.info("Admin user already exists")

def main():
    """Main setup function"""
    logger.info("Starting database setup...")
    
    try:
        # Create tables
        engine = create_database_tables()
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Load configuration
        config_path = project_root / 'config.yaml'
        if not config_path.exists():
            logger.error("config.yaml not found!")
            return False
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Populate data
        populate_properties(session, config_data)
        populate_users_and_meters(session, config_data)
        create_admin_user(session)
        
        session.close()
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
