from sqlalchemy import case, func, select

from app.models import Recommendation

PRIORITY_ORDER = case(
    (Recommendation.priority == "High", 0),
    (Recommendation.priority == "Medium", 1),
    else_=2,
)


def count_rows(session, model):
    return session.scalar(select(func.count()).select_from(model)) or 0


def paginate(session, statement, page, page_size):
    total = session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    ) or 0
    offset = (page - 1) * page_size
    rows = session.scalars(statement.offset(offset).limit(page_size)).all()
    return total, rows


def count_by_label(session, column, labels):
    counts = dict(session.execute(select(column, func.count()).group_by(column)).all())
    return {label: counts.get(label, 0) for label in labels}
