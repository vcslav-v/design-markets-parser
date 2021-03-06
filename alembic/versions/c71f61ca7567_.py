"""empty message

Revision ID: c71f61ca7567
Revises: 2da71b65e2e3
Create Date: 2021-11-24 10:23:05.532855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c71f61ca7567'
down_revision = '0da15022a0f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('creators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('products', sa.Column('creator_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'products', 'creators', ['creator_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.drop_column('products', 'creator_id')
    op.drop_table('creators')
    # ### end Alembic commands ###
