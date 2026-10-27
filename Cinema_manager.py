from datetime import date, datetime

from Models import Movie, Ticket, Showtime
from File_helper import FileHelper


class CinemaManager:
    """Quản lý phim, đặt vé và thống kê; phần giao diện nằm ở lớp khác."""

    def __init__(self):
        # Dùng mã làm khóa để tìm phim hoặc vé trực tiếp trong dictionary.
        self.movies = {}
        self.tickets = {}
        self.showtimes = {}
        self._file_helper = FileHelper()

    def addMovie(self, movie: Movie, first_showtime: Showtime | None = None):
        if movie.movie_id in self.movies:
            raise ValueError("Movie ID already exists")
        # Kiểm tra cả phim và suất đầu tiên trước khi lưu vào bộ nhớ.
        if first_showtime is not None:
            if first_showtime.movie_id != movie.movie_id:
                raise ValueError("Showtime must belong to the new movie")
            if first_showtime.showtime_id in self.showtimes:
                raise ValueError("Showtime ID already exists")
        self.movies[movie.movie_id] = movie
        if first_showtime is not None:
            self.showtimes[first_showtime.showtime_id] = first_showtime
        return movie

    def searchMovie(self, query: str):
        query = query.strip().casefold()
        if not query:
            return []
        matching_movies = []
        for movie in self.movies.values():
            if (query in movie.movie_id.casefold()
                    or query in movie.title.casefold()
                    or query in movie.genre.casefold()):
                matching_movies.append(movie)
        return matching_movies

    def deleteMovie(self, movie_id: str):
        if movie_id not in self.movies:
            if movie_id in self.showtimes:
                correct_id = self.showtimes[movie_id].movie_id
                raise ValueError(f"This is a showtime ID. Use Movie ID {correct_id}; option 14 deletes one time")
            raise ValueError("Movie not found")
        if any(ticket.movie_id == movie_id for ticket in self.tickets.values()):
            raise ValueError("Cannot delete a movie with ticket history")
        del self.movies[movie_id]
        self.showtimes = {key: show for key, show in self.showtimes.items()
                          if show.movie_id != movie_id}

    def addShowtime(self, showtime: Showtime):
        if showtime.showtime_id in self.showtimes:
            raise ValueError("Showtime ID already exists")
        if showtime.movie_id not in self.movies:
            raise ValueError("Movie not found")
        self.showtimes[showtime.showtime_id] = showtime
        return showtime

    def deleteShowtime(self, showtime_id: str):
        """Chỉ xóa một suất chưa có lịch sử vé, giữ nguyên phim và các suất khác."""
        self._showtime(showtime_id)
        for ticket in self.tickets.values():
            if ticket.showtime_id == showtime_id:
                raise ValueError("Cannot delete a showtime with ticket history")
        del self.showtimes[showtime_id]

    def listShowtimes(self, movie_id=None):
        shows = []
        for show in self.showtimes.values():
            if movie_id is None or show.movie_id == movie_id:
                shows.append(show)
        return sorted(shows, key=lambda show: datetime.strptime(show.starts_at, "%H:%M - %d/%m/%Y"))

    def _showtime(self, showtime_id):
        show = self.showtimes.get(showtime_id)
        if show is None:
            raise ValueError("Showtime not found")
        return show

    def availableShowtimeSeats(self, showtime_id):
        show = self._showtime(showtime_id)
        booked_seats = set()
        for ticket in self.tickets.values():
            if ticket.showtime_id == showtime_id and ticket.status != "Cancelled":
                booked_seats.add(ticket.seat_number)
        return [seat for seat in show.seat_numbers() if seat not in booked_seats]

    def bookSeats(self, showtime_id, seat_numbers):
        """Kiểm tra toàn bộ yêu cầu trước, rồi mới lưu vé cho từng ghế."""
        show = self._showtime(showtime_id)
        if self.movies[show.movie_id].status != "Showing":
            raise ValueError("Movie is not showing")
        seats = [seat.strip().upper() for seat in seat_numbers]
        if not seats or len(seats) != len(set(seats)):
            raise ValueError("Choose at least one seat, without duplicates")
        available = self.availableShowtimeSeats(showtime_id)
        for seat in seats:
            if seat not in available:
                raise ValueError(f"Seat {seat} is invalid or already booked")

        tickets = []
        next_number = 1
        for seat in seats:
            while f"T{next_number:05d}" in self.tickets:
                next_number += 1
            ticket = Ticket(f"T{next_number:05d}", show.movie_id, seat,
                            date.today(), "Booked", show.ticket_price, showtime_id)
            tickets.append(ticket)
            next_number += 1
        for ticket in tickets:
            self.tickets[ticket.ticket_id] = ticket
        return tickets

    def _active_tickets(self, movie_id: str):
        """Vé chưa hủy vẫn chiếm ghế, kể cả vé đã Checked-In."""
        active_tickets = []
        for ticket in self.tickets.values():
            if ticket.movie_id == movie_id and ticket.status != "Cancelled":
                active_tickets.append(ticket)
        return active_tickets

    def availableSeats(self, movie_id: str):
        movie = self.movies.get(movie_id)
        if movie is None:
            raise ValueError("Movie not found")
        shows = self.listShowtimes(movie_id)
        if shows:
            return sum(len(self.availableShowtimeSeats(show.showtime_id)) for show in shows)
        return movie.total_seats - len(self._legacy_tickets(movie_id))

    def _legacy_tickets(self, movie_id):
        return [ticket for ticket in self._active_tickets(movie_id)
                if ticket.showtime_id is None]

    def createTicket(self, ticket_id: str, movie_id: str, seat_number: str,
                     purchase_date: date | None = None):
        if ticket_id in self.tickets:
            raise ValueError("Ticket ID already exists")
        movie = self.movies.get(movie_id)
        if movie is None:
            raise ValueError("Movie not found")
        if self.listShowtimes(movie_id):
            raise ValueError("Choose a showtime and use bookSeats")
        if movie.status != "Showing":
            raise ValueError("Movie is not showing")
        seat_number = seat_number.strip().upper()
        if not seat_number:
            raise ValueError("Seat number is required")
        active_tickets = self._legacy_tickets(movie_id)
        for existing_ticket in active_tickets:
            if existing_ticket.seat_number == seat_number:
                raise ValueError("Seat is already booked")
        if len(active_tickets) >= movie.total_seats:
            raise ValueError("Sold out")
        # Lưu giá lúc mua để doanh thu cũ không đổi khi giá phim thay đổi.
        ticket = Ticket(
            ticket_id=ticket_id,
            movie_id=movie_id,
            seat_number=seat_number,
            purchase_date=purchase_date or date.today(),
            status="Booked",
            price_paid=movie.ticket_price,
        )
        self.tickets[ticket_id] = ticket
        return ticket

    def updateTicket(self, ticket_id: str, seat_number: str | None = None,
                     status: str | None = None):
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise ValueError("Ticket not found")
        if ticket.status != "Booked":
            raise ValueError("Only booked tickets can be changed")
        # Mỗi lần chỉ được đổi ghế hoặc đổi trạng thái.
        if seat_number is None and status is None:
            raise ValueError("Change either the seat or the status")
        if seat_number is not None and status is not None:
            raise ValueError("Change either the seat or the status")
        if seat_number is not None:
            seat_number = seat_number.strip().upper()
            if not seat_number:
                raise ValueError("Seat number is required")
            if ticket.showtime_id is not None:
                show = self._showtime(ticket.showtime_id)
                if seat_number not in show.seat_numbers():
                    raise ValueError("Invalid seat number for this showtime")
            for other_ticket in self._active_tickets(ticket.movie_id):
                if other_ticket.showtime_id != ticket.showtime_id:
                    continue
                if other_ticket.ticket_id == ticket_id:
                    continue
                if other_ticket.seat_number == seat_number:
                    raise ValueError("Seat is already booked")
            ticket.seat_number = seat_number
        elif status in {"Cancelled", "Checked-In"}:
            ticket.status = status
        else:
            raise ValueError("Status must be Cancelled or Checked-In")
        return ticket

    def displayTicketSales(self):
        sales = []
        for movie_id in self.movies:
            ticket_count = len(self._active_tickets(movie_id))
            sales.append((movie_id, ticket_count))
        # Số vé giảm dần; nếu bằng nhau thì mã phim tăng dần.
        return sorted(sales, key=lambda item: (-item[1], item[0]))

    def displayHighestSellingMovies(self):
        sales = self.displayTicketSales()
        if not sales or sales[0][1] == 0:
            return []
        highest_count = sales[0][1]
        return [sale for sale in sales if sale[1] == highest_count]

    def displayMonthlyRevenue(self, month: int | None = None, year: int | None = None):
        today = date.today()
        if month is None:
            month = today.month
        if year is None:
            year = today.year
        if not 1 <= month <= 12 or year <= 0:
            raise ValueError("Invalid month or year")
        revenue = {movie_id: 0 for movie_id in self.movies}
        for ticket in self.tickets.values():
            if (ticket.status != "Cancelled" and
                    ticket.purchase_date.month == month and
                    ticket.purchase_date.year == year):
                revenue[ticket.movie_id] += ticket.price_paid
        return sorted(revenue.items(), key=lambda item: (-item[1], item[0]))

    def to_dict(self):
        return {
            "movies": [movie.to_dict() for movie in self.movies.values()],
            "tickets": [ticket.to_dict() for ticket in self.tickets.values()],
            "showtimes": [show.to_dict() for show in self.showtimes.values()],
        }

    def saveData(self, path):
        self._file_helper.save(path, self.to_dict())

    def loadData(self, path):
        data = self._file_helper.load(path)
        try:
            if not isinstance(data, dict) or set(data) not in (
                    {"movies", "tickets"}, {"movies", "tickets", "showtimes"}):
                raise ValueError("Invalid data file structure")
            if not isinstance(data["movies"], list) or not isinstance(data["tickets"], list):
                raise ValueError("Movies and tickets must be lists")
            # Kiểm tra trên bộ dữ liệu tạm. File lỗi sẽ không làm mất dữ liệu cũ.
            restored = CinemaManager()
            for item in data["movies"]:
                restored.addMovie(Movie(**item))
            if not isinstance(data.get("showtimes", []), list):
                raise ValueError("Showtimes must be a list")
            for item in data.get("showtimes", []):
                restored.addShowtime(Showtime(**item))
            for item in data["tickets"]:
                ticket = Ticket.from_dict(item)
                if ticket.ticket_id in restored.tickets:
                    raise ValueError("Duplicate ticket ID in data file")
                if ticket.movie_id not in restored.movies:
                    raise ValueError("Ticket refers to an unknown movie")
                if ticket.showtime_id is not None:
                    show = restored._showtime(ticket.showtime_id)
                    if show.movie_id != ticket.movie_id or ticket.seat_number not in show.seat_numbers():
                        raise ValueError("Ticket does not match its showtime")
                if ticket.status != "Cancelled":
                    if ticket.showtime_id is not None:
                        if ticket.seat_number not in restored.availableShowtimeSeats(ticket.showtime_id):
                            raise ValueError("Duplicate booked seat in data file")
                    else:
                        legacy = restored._legacy_tickets(ticket.movie_id)
                        if len(legacy) >= restored.movies[ticket.movie_id].total_seats:
                            raise ValueError("Too many active tickets in data file")
                        if any(other.seat_number == ticket.seat_number for other in legacy):
                            raise ValueError("Duplicate booked seat in data file")
                restored.tickets[ticket.ticket_id] = ticket
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("Invalid data file contents") from error
        self.movies = restored.movies
        self.tickets = restored.tickets
        self.showtimes = restored.showtimes
