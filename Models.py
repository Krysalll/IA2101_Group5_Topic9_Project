from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass
class Movie:
    movie_id: str
    title: str
    genre: str
    duration_minutes: int
    release_year: int
    showtime: str
    ticket_price: int  # VND
    status: str
    total_seats: int

    def __post_init__(self):
        if not self.movie_id.strip() or not self.title.strip() or not self.genre.strip():
            raise ValueError("Movie ID, title and genre are required")
        if self.duration_minutes <= 0 or self.release_year <= 0:
            raise ValueError("Duration and release year must be positive")
        if self.ticket_price < 0 or self.total_seats <= 0:
            raise ValueError("Price must be non-negative and seats must be positive")
        if self.status not in {"Showing", "Ended"}:
            raise ValueError("Movie status must be Showing or Ended")

    def to_dict(self):
        return asdict(self)


@dataclass
class Showtime:
    """Một lần chiếu phim, có phòng, sơ đồ ghế và giá vé riêng."""

    showtime_id: str
    movie_id: str
    starts_at: str
    room: str
    rows: int
    seats_per_row: int
    ticket_price: int

    def __post_init__(self):
        if not self.showtime_id.strip() or not self.movie_id.strip() or not self.room.strip():
            raise ValueError("Showtime ID, movie ID and room are required")
        datetime.strptime(self.starts_at, "%H:%M - %d/%m/%Y")
        if not 1 <= self.rows <= 26 or not 1 <= self.seats_per_row <= 50:
            raise ValueError("Use 1-26 rows and 1-50 seats per row")
        if self.ticket_price < 0:
            raise ValueError("Ticket price cannot be negative")

    def seat_numbers(self):
        # Ví dụ: 2 hàng, mỗi hàng 3 ghế -> A01, A02, A03, B01, B02, B03.
        seats = []
        for row in range(self.rows):
            row_name = chr(ord("A") + row)
            for number in range(1, self.seats_per_row + 1):
                seats.append(f"{row_name}{number:02d}")
        return seats

    def to_dict(self):
        return asdict(self)


@dataclass
class Ticket:
    ticket_id: str
    movie_id: str
    seat_number: str
    purchase_date: date
    status: str
    price_paid: int  # Price at purchase time, in VND
    showtime_id: str | None = None  # None dành cho vé của phiên bản cũ.

    def __post_init__(self):
        if not self.ticket_id.strip() or not self.movie_id.strip() or not self.seat_number.strip():
            raise ValueError("Ticket ID, movie ID and seat number are required")
        if not isinstance(self.purchase_date, date):
            raise ValueError("Purchase date must be a date")
        if self.status not in {"Booked", "Cancelled", "Checked-In"}:
            raise ValueError("Invalid ticket status")
        if self.price_paid < 0:
            raise ValueError("Ticket price cannot be negative")

    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "movie_id": self.movie_id,
            "seat_number": self.seat_number,
            "purchase_date": self.purchase_date.isoformat(),
            "status": self.status,
            "price_paid": self.price_paid,
            "showtime_id": self.showtime_id,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ticket_id=data["ticket_id"],
            movie_id=data["movie_id"],
            seat_number=data["seat_number"],
            purchase_date=date.fromisoformat(data["purchase_date"]),
            status=data["status"],
            price_paid=data["price_paid"],
            showtime_id=data.get("showtime_id"),
        )
