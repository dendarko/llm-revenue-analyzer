"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-25 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "llm_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cost_usd", sa.Numeric(14, 6), nullable=False),
        sa.Column("feature", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_events_timestamp", "llm_events", ["timestamp"])
    op.create_index("ix_llm_events_tenant_id", "llm_events", ["tenant_id"])
    op.create_index("ix_llm_events_request_id", "llm_events", ["request_id"])
    op.create_index("ix_llm_events_model", "llm_events", ["model"])
    op.create_index("ix_llm_events_provider", "llm_events", ["provider"])
    op.create_index("ix_llm_events_feature", "llm_events", ["feature"])
    op.create_index("ix_llm_events_tenant_timestamp", "llm_events", ["tenant_id", "timestamp"])

    op.create_table(
        "revenue_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("amount_usd", sa.Numeric(14, 6), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_revenue_events_timestamp", "revenue_events", ["timestamp"])
    op.create_index("ix_revenue_events_tenant_id", "revenue_events", ["tenant_id"])
    op.create_index("ix_revenue_events_source", "revenue_events", ["source"])
    op.create_index("ix_revenue_events_tenant_timestamp", "revenue_events", ["tenant_id", "timestamp"])

    op.create_table(
        "budgets",
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("monthly_budget_usd", sa.Numeric(14, 6), nullable=False),
        sa.Column("hard_limit", sa.Boolean(), nullable=False),
        sa.Column("soft_limit_pct", sa.Numeric(5, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_tenant_id", "alerts", ["tenant_id"])
    op.create_index("ix_alerts_type", "alerts", ["type"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index("ix_alerts_tenant_created", "alerts", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_tenant_created", table_name="alerts")
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_type", table_name="alerts")
    op.drop_index("ix_alerts_tenant_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("budgets")

    op.drop_index("ix_revenue_events_tenant_timestamp", table_name="revenue_events")
    op.drop_index("ix_revenue_events_source", table_name="revenue_events")
    op.drop_index("ix_revenue_events_tenant_id", table_name="revenue_events")
    op.drop_index("ix_revenue_events_timestamp", table_name="revenue_events")
    op.drop_table("revenue_events")

    op.drop_index("ix_llm_events_tenant_timestamp", table_name="llm_events")
    op.drop_index("ix_llm_events_feature", table_name="llm_events")
    op.drop_index("ix_llm_events_provider", table_name="llm_events")
    op.drop_index("ix_llm_events_model", table_name="llm_events")
    op.drop_index("ix_llm_events_request_id", table_name="llm_events")
    op.drop_index("ix_llm_events_tenant_id", table_name="llm_events")
    op.drop_index("ix_llm_events_timestamp", table_name="llm_events")
    op.drop_table("llm_events")

    op.drop_table("tenants")
