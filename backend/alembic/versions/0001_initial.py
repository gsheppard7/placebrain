"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "zones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("space_id", sa.String(length=36), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_zone_id", sa.String(length=36), sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_zones_space_id", "zones", ["space_id"])
    op.create_table(
        "scans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("space_id", sa.String(length=36), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status in ('manual', 'imported')", name="ck_scans_status"),
    )
    op.create_index("ix_scans_space_id", "scans", ["space_id"])
    op.create_table(
        "scene_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scan_id", sa.String(length=36), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("storage_uri", sa.String(length=1000), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("alignment_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "asset_type in ('procedural', 'glb', 'gaussian_splat')",
            name="ck_scene_assets_type",
        ),
    )
    op.create_index("ix_scene_assets_scan_id", "scene_assets", ["scan_id"])
    op.create_table(
        "inventory_objects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("space_id", sa.String(length=36), sa.ForeignKey("spaces.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_inventory_objects_space_id", "inventory_objects", ["space_id"])
    op.create_table(
        "object_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("object_id", sa.String(length=36), sa.ForeignKey("inventory_objects.id"), nullable=False),
        sa.Column("scan_id", sa.String(length=36), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("zone_id", sa.String(length=36), sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("z", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("source in ('manual', 'model')", name="ck_observations_source"),
    )
    op.create_index("ix_object_observations_object_id", "object_observations", ["object_id"])
    op.create_index("ix_object_observations_scan_id", "object_observations", ["scan_id"])
    op.create_table(
        "annotations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("object_id", sa.String(length=36), sa.ForeignKey("inventory_objects.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("external_url", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_annotations_object_id", "annotations", ["object_id"])


def downgrade() -> None:
    op.drop_table("annotations")
    op.drop_table("object_observations")
    op.drop_table("inventory_objects")
    op.drop_table("scene_assets")
    op.drop_table("scans")
    op.drop_table("zones")
    op.drop_table("spaces")
