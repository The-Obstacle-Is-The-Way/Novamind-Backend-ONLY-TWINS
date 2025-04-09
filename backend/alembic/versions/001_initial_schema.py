# -*- coding: utf-8 -*-
"""Initial database schema for NOVAMIND

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-03-26 11:33:00.000000

This migration creates the initial database schema for the NOVAMIND application,
including the core patient and digital twin tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(50), nullable=True),
        sa.Column('insurance_provider', sa.String(100), nullable=True),
        sa.Column('insurance_policy_number', sa.String(100), nullable=True),
        sa.Column('insurance_group_number', sa.String(100), nullable=True),
        sa.Column('active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )
    
    # Create providers table
    op.create_table(
        'providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=False),
        sa.Column('license_number', sa.String(100), nullable=False),
        sa.Column('npi_number', sa.String(20), nullable=True),
        sa.Column('active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('appointment_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('virtual', sa.Boolean(), default=False, nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create medications table
    op.create_table(
        'medications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create clinical_notes table
    op.create_table(
        'clinical_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id'), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('appointments.id'), nullable=True),
        sa.Column('note_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
    )
    
    # Create digital_twins table
    op.create_table(
        'digital_twins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_forecast_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
    )
    
    # Create digital_twin_data table for storing time series data
    op.create_table(
        'digital_twin_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('digital_twin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('digital_twins.id'), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create digital_twin_forecasts table
    op.create_table(
        'digital_twin_forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('digital_twin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('digital_twins.id'), nullable=False),
        sa.Column('forecast_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('forecast_data', postgresql.JSONB, nullable=False),
        sa.Column('confidence_scores', postgresql.JSONB, nullable=False),
        sa.Column('contributing_factors', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_patients_email', 'patients', ['email'], unique=True)
    op.create_index('ix_patients_last_name', 'patients', ['last_name'])
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_start_time', 'appointments', ['start_time'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_medications_patient_id', 'medications', ['patient_id'])
    op.create_index('ix_clinical_notes_patient_id', 'clinical_notes', ['patient_id'])
    op.create_index('ix_digital_twin_data_digital_twin_id', 'digital_twin_data', ['digital_twin_id'])
    op.create_index('ix_digital_twin_data_timestamp', 'digital_twin_data', ['timestamp'])
    op.create_index('ix_digital_twin_forecasts_digital_twin_id', 'digital_twin_forecasts', ['digital_twin_id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('digital_twin_forecasts')
    op.drop_table('digital_twin_data')
    op.drop_table('digital_twins')
    op.drop_table('clinical_notes')
    op.drop_table('medications')
    op.drop_table('appointments')
    op.drop_table('providers')
    op.drop_table('patients')
    op.drop_table('users')