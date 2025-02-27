from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Concept(Base):
    __tablename__ = "concept"

    id_: Mapped[str] = mapped_column(primary_key=True)
    types: Mapped[list] = mapped_column(JSON)
    pref_labels: Mapped[list] = mapped_column(JSON)
    schemes: Mapped[list] = mapped_column(JSON)
    definitions: Mapped[list] = mapped_column(JSON)
    notations: Mapped[list] = mapped_column(JSON)
    alt_labels: Mapped[list] = mapped_column(JSON)
    hidden_labels: Mapped[list] = mapped_column(JSON)
    change_notes: Mapped[list] = mapped_column(JSON)
    history_notes: Mapped[list] = mapped_column(JSON)
    editorial_notes: Mapped[list] = mapped_column(JSON)
    extra: Mapped[dict] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"Concept(id={self.id_})"
