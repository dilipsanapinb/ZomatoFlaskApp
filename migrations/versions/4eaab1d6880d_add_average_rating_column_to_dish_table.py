"""Add average_rating column to Dish table

Revision ID: 4eaab1d6880d
Revises: 16eb6836e455
Create Date: 2023-07-13 01:36:50.640686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4eaab1d6880d'
down_revision = '16eb6836e455'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rating',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('dish_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dish_id'], ['dish.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('dish', schema=None) as batch_op:
        batch_op.add_column(sa.Column('average_rating', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dish', schema=None) as batch_op:
        batch_op.drop_column('average_rating')

    op.drop_table('rating')
    # ### end Alembic commands ###
