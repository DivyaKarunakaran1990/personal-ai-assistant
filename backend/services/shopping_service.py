from sqlalchemy.orm import Session

from models import ShoppingItem


def add_item(db: Session, item: str):

    item = item.strip()

    existing_item = (
        db.query(ShoppingItem)
        .filter(
            ShoppingItem.item.ilike(item)
        )
        .first()
    )

    if existing_item:
        return None

    shopping_item = ShoppingItem(
        item=item,
        completed=False
    )

    db.add(shopping_item)
    db.commit()
    db.refresh(shopping_item)

    return shopping_item
    
def get_items(db: Session):

    return db.query(ShoppingItem).all()


def remove_item(db: Session, item_name: str):

    item = (
        db.query(ShoppingItem)
        .filter(ShoppingItem.item.ilike(item_name.strip()))
        .first()
    )

    if not item:
        return None

    db.delete(item)
    db.commit()

    return item