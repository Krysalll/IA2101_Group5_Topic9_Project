"""Console entry point for the movie ticket purchase project."""

import tempfile
from pathlib import Path

from Cinema_manager import CinemaManager
from Console_io import ConsoleIO
from Models import Movie, Showtime


DATA_FILE = Path(__file__).with_name("cinema_data.txt")


def read_showtime(io, manager, movie_id, ticket_price=None):
    """Người dùng chỉ nhập mã phim; mã suất được chương trình tự tạo."""
    number = 1
    while f"{movie_id}-{number:02d}" in manager.showtimes:
        number += 1
    starts_at = io.read_string("Start (HH:MM - DD/MM/YYYY): ")
    room = io.read_string("Room: ")
    rows = io.read_int("Number of rows (1-26): ")
    seats_per_row = io.read_int("Seats per row (1-50): ")
    if ticket_price is None:
        ticket_price = io.read_int("Price per seat (VND): ")
    return Showtime(f"{movie_id}-{number:02d}", movie_id, starts_at,
                    room, rows, seats_per_row, ticket_price)


def book_tickets(io, manager):
    """Luồng khách hàng: chọn suất -> xem ghế -> đặt nhiều ghế."""
    if not manager.showtimes:
        print("No showtimes. Add a movie with its first showtime (1), or load data (10).")
        return
    show = io.choose_showtime(manager)
    if show is None:
        return
    showtime_id = show.showtime_id
    io.display_seats(showtime_id, manager)
    selected = io.read_string("Seats, separated by commas (e.g. A01,A02; blank to go back): ")
    if not selected:
        return
    tickets = manager.bookSeats(showtime_id, selected.split(","))
    movie = manager.movies[show.movie_id]
    print(f"Booked: {movie.title} | {show.starts_at} | {show.room}")
    for ticket in tickets:
        print(f"Ticket {ticket.ticket_id} | Seat {ticket.seat_number} | {ticket.price_paid:,} VND")
    total = sum(ticket.price_paid for ticket in tickets)
    print(f"Total: {total:,} VND")
    print("Use option 9 to save your bookings before exiting.")


def test_file_io(manager):
    """Save and reload a copy without changing the live data file."""
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
        path = Path(directory) / "io_test.txt"
        manager.saveData(path)
        copy = CinemaManager()
        copy.loadData(path)
        return copy.to_dict() == manager.to_dict()


def main():
    io = ConsoleIO()
    manager = CinemaManager()
    # Tự đọc dữ liệu một lần khi khởi động, trước khi hiển thị menu.
    try:
        manager.loadData(DATA_FILE)
        print(f"Automatically loaded {len(manager.movies)} movies, "
              f"{len(manager.showtimes)} showtimes and {len(manager.tickets)} tickets.")
    except FileNotFoundError:
        print("No saved data file. Starting with empty data; use option 9 to save.")
    except (ValueError, OSError) as error:
        print(f"Could not load saved data: {error}")
        print("Starting with empty data. Check the data file before saving.")
    while True:
        io.show_menu()
        choice = io.read_int("Enter your choice: ")
        try:
            if choice == 1:
                movie = Movie(
                    movie_id=io.read_string("Movie ID: "),
                    title=io.read_string("Title: "),
                    genre=io.read_string("Genre: "),
                    duration_minutes=io.read_int("Duration (minutes): "),
                    release_year=io.read_int("Release year: "),
                    showtime="",  # Giữ trường cũ để đọc được dữ liệu phiên bản trước.
                    ticket_price=io.read_int("Ticket price (VND): "),
                    status=io.read_string("Status (Showing/Ended): "),
                    total_seats=1,  # Số ghế thực tế được khai báo riêng cho từng suất.
                )
                if movie.movie_id in manager.movies:
                    raise ValueError("Movie ID already exists")
                print("Enter the first showtime for this movie:")
                show = read_showtime(io, manager, movie.movie_id, movie.ticket_price)
                movie.showtime = show.starts_at
                movie.total_seats = show.rows * show.seats_per_row
                manager.addMovie(movie, first_showtime=show)
                print(f"Movie {movie.movie_id} and its first showtime added. View in option 13.")
            elif choice == 2:
                io.display_movies(manager.searchMovie(io.read_string("ID, title or genre: ")), manager)
            elif choice == 3:
                io.display_movies(list(manager.movies.values()), manager)
                movie_id = io.read_string("Movie ID to delete (e.g. M00007; blank to go back): ")
                if not movie_id:
                    continue
                manager.deleteMovie(movie_id)
                print(f"Movie {movie_id} and its showtimes deleted. Use option 9 to save.")
            elif choice == 4:
                book_tickets(io, manager)
            elif choice == 5:
                ticket_id = io.read_string("Ticket ID: ")
                action = io.read_int("1=Change seat, 2=Cancel, 3=Check in: ")
                if action == 1:
                    ticket = manager.updateTicket(ticket_id, seat_number=io.read_string("New seat: "))
                elif action == 2:
                    ticket = manager.updateTicket(ticket_id, status="Cancelled")
                elif action == 3:
                    ticket = manager.updateTicket(ticket_id, status="Checked-In")
                else:
                    print("Invalid action.")
                    continue
                print(f"Ticket {ticket.ticket_id}: {ticket.status}, seat {ticket.seat_number}.")
            elif choice == 6:
                io.display_totals(manager.displayHighestSellingMovies(), manager, "tickets")
            elif choice == 7:
                io.display_totals(manager.displayTicketSales(), manager, "tickets")
            elif choice == 8:
                io.display_totals(manager.displayMonthlyRevenue(), manager, "VND")
            elif choice == 9:
                manager.saveData(DATA_FILE)
                print(f"Saved to {DATA_FILE}.")
            elif choice == 10:
                manager.loadData(DATA_FILE)
                print(f"Loaded from {DATA_FILE}.")
            elif choice == 11:
                print("I/O test PASS" if test_file_io(manager) else "I/O test FAIL")
            elif choice == 12:
                io.display_movies(list(manager.movies.values()), manager)
                movie_id = io.read_string("Movie ID to add a showtime (blank to go back): ")
                if not movie_id:
                    continue
                if movie_id not in manager.movies:
                    raise ValueError("Movie not found")
                show = read_showtime(io, manager, movie_id)
                manager.addShowtime(show)
                print(f"Showtime for {movie_id} added. View in option 13.")
            elif choice == 13:
                show = io.choose_showtime(manager)
                if show is not None:
                    io.display_seats(show.showtime_id, manager)
            elif choice == 14:
                show = io.choose_showtime(manager)
                if show is not None:
                    manager.deleteShowtime(show.showtime_id)
                    print(f"Showtime for {show.movie_id} at {show.starts_at} deleted. Use option 9 to save.")
            elif choice == 0:
                print("Goodbye.")
                break
            else:
                print("Invalid menu choice.")
        except (ValueError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
