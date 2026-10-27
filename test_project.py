import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from datetime import date
from pathlib import Path

from Cinema_manager import CinemaManager
from Main import main, test_file_io as run_file_io_check
from Models import Movie, Showtime


def sample_movie(movie_id="M00001", price=75000, seats=2):
    return Movie(
        movie_id=movie_id,
        title="Python Cinema",
        genre="Comedy",
        duration_minutes=100,
        release_year=2026,
        showtime="19:00 - 25/10/2026",
        ticket_price=price,
        status="Showing",
        total_seats=seats,
    )


class CinemaManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = CinemaManager()
        self.manager.addMovie(sample_movie())

    def test_movie_search_and_delete_protects_ticket_history(self):
        self.assertEqual(len(self.manager.searchMovie("python")), 1)
        self.assertEqual(len(self.manager.searchMovie("comedy")), 1)
        self.manager.createTicket("T00001", "M00001", "A01")
        with self.assertRaises(ValueError):
            self.manager.deleteMovie("M00001")
        self.manager.updateTicket("T00001", status="Cancelled")
        with self.assertRaises(ValueError):
            self.manager.deleteMovie("M00001")

    def test_ticket_rejects_duplicate_id_seat_and_sold_out(self):
        self.manager.createTicket("T00001", "M00001", "A01")
        with self.assertRaises(ValueError):
            self.manager.createTicket("T00001", "M00001", "A02")
        with self.assertRaises(ValueError):
            self.manager.createTicket("T00002", "M00001", "A01")
        self.manager.createTicket("T00002", "M00001", "A02")
        with self.assertRaises(ValueError):
            self.manager.createTicket("T00003", "M00001", "A03")
        self.assertEqual(self.manager.availableSeats("M00001"), 0)

    def test_cancel_releases_seat_and_revenue_keeps_purchase_price(self):
        today = date.today()
        self.manager.createTicket("T00001", "M00001", "A01", today)
        self.manager.createTicket("T00002", "M00001", "A02", today)
        self.manager.updateTicket("T00001", status="Cancelled")
        self.assertEqual(self.manager.availableSeats("M00001"), 1)
        self.manager.createTicket("T00003", "M00001", "A01", today)
        self.manager.movies["M00001"].ticket_price = 90000
        self.assertEqual(self.manager.displayMonthlyRevenue(today.month, today.year), [("M00001", 150000)])
        self.assertEqual(self.manager.displayTicketSales(), [("M00001", 2)])

    def test_update_seat_and_check_in(self):
        self.manager.createTicket("T00001", "M00001", "A01")
        self.manager.updateTicket("T00001", seat_number="B01")
        self.assertEqual(self.manager.tickets["T00001"].seat_number, "B01")
        self.manager.updateTicket("T00001", status="Checked-In")
        with self.assertRaises(ValueError):
            self.manager.updateTicket("T00001", status="Cancelled")
        with self.assertRaises(ValueError):
            self.manager.updateTicket("T00001", seat_number="A01")

    def test_sales_are_sorted_and_highest_includes_ties(self):
        self.manager.addMovie(sample_movie("M00002"))
        self.manager.createTicket("T00001", "M00001", "A01")
        self.manager.createTicket("T00002", "M00002", "A01")
        self.assertEqual(self.manager.displayHighestSellingMovies(), [("M00001", 1), ("M00002", 1)])
        self.manager.createTicket("T00003", "M00002", "A02")
        self.assertEqual(self.manager.displayTicketSales(), [("M00002", 2), ("M00001", 1)])

    def test_file_io_round_trip_and_errors(self):
        self.manager.createTicket("T00001", "M00001", "A01")
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "cinema_data.txt"
            self.manager.saveData(path)
            restored = CinemaManager()
            restored.loadData(path)
            self.assertEqual(restored.to_dict(), self.manager.to_dict())
            with self.assertRaises(FileNotFoundError):
                restored.loadData(Path(directory) / "missing.txt")
            path.write_text("not valid json", encoding="utf-8")
            with self.assertRaises(ValueError):
                restored.loadData(path)
            self.assertEqual(restored.to_dict(), self.manager.to_dict())

    def test_main_menu_file_io_check(self):
        self.manager.createTicket("T00001", "M00001", "A01")
        before = self.manager.to_dict()
        self.assertTrue(run_file_io_check(self.manager))
        self.assertEqual(self.manager.to_dict(), before)


class ShowtimeTests(unittest.TestCase):
    def setUp(self):
        # Mỗi kiểm thử dùng file riêng, không tự tải dữ liệu thật của người dùng.
        directory = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(directory.cleanup)
        data_file = patch("Main.DATA_FILE", Path(directory.name) / "cinema_data.txt")
        data_file.start()
        self.addCleanup(data_file.stop)
        self.manager = CinemaManager()
        self.manager.addMovie(sample_movie())
        for show_id, time in [("S01", "18:30"), ("S02", "20:30")]:
            self.manager.addShowtime(Showtime(
                show_id, "M00001", f"{time} - 30/10/2026", "Room 1", 2, 3, 75000
            ))

    def test_two_seats_and_independent_showtimes(self):
        tickets = self.manager.bookSeats("S01", [" a01 ", "A02"])
        self.assertEqual(len(tickets), 2)
        self.assertEqual(self.manager.availableShowtimeSeats("S01"), ["A03", "B01", "B02", "B03"])
        self.assertIn("A01", self.manager.availableShowtimeSeats("S02"))
        self.manager.bookSeats("S02", ["A01"])
        self.assertEqual(self.manager.displayTicketSales(), [("M00001", 3)])
        self.assertEqual(self.manager.availableSeats("M00001"), 9)

    def test_delete_showtime_keeps_movie_and_other_showtimes(self):
        self.manager.deleteShowtime("S01")
        self.assertNotIn("S01", self.manager.showtimes)
        self.assertIn("S02", self.manager.showtimes)
        self.assertIn("M00001", self.manager.movies)
        with self.assertRaisesRegex(ValueError, "Showtime not found"):
            self.manager.deleteShowtime("UNKNOWN")

    def test_delete_showtime_protects_ticket_history(self):
        ticket = self.manager.bookSeats("S01", ["A01"])[0]
        with self.assertRaisesRegex(ValueError, "ticket history"):
            self.manager.deleteShowtime("S01")
        self.manager.updateTicket(ticket.ticket_id, status="Cancelled")
        with self.assertRaisesRegex(ValueError, "ticket history"):
            self.manager.deleteShowtime("S01")

    def test_delete_movie_with_showtime_id_gives_guidance(self):
        with self.assertRaisesRegex(ValueError, "showtime ID.*option 14"):
            self.manager.deleteMovie("S01")
        self.assertIn("M00001", self.manager.movies)
        self.assertIn("S01", self.manager.showtimes)

    def test_console_delete_showtime(self):
        output = StringIO()
        with patch("Main.CinemaManager", return_value=self.manager), \
                patch("builtins.input", side_effect=["14", "M00001", "1", "0"]), \
                redirect_stdout(output):
            main()
        self.assertIn("Showtime for M00001 at 18:30", output.getvalue())
        self.assertNotIn("S01", self.manager.showtimes)
        self.assertIn("M00001", self.manager.movies)

    def test_invalid_group_booking_creates_no_partial_tickets(self):
        self.manager.bookSeats("S01", ["A02"])
        before = self.manager.to_dict()
        for seats in (["A01", "A02"], ["A01", "Z99"], ["A01", "a01"], []):
            with self.assertRaises(ValueError):
                self.manager.bookSeats("S01", seats)
            self.assertEqual(self.manager.to_dict(), before)

    def test_cancel_and_change_seat_are_scoped_to_showtime(self):
        first = self.manager.bookSeats("S01", ["A01"])[0]
        self.manager.bookSeats("S02", ["A02"])
        self.manager.updateTicket(first.ticket_id, seat_number="A02")
        with self.assertRaises(ValueError):
            self.manager.updateTicket(first.ticket_id, seat_number="Z99")
        self.manager.updateTicket(first.ticket_id, status="Cancelled")
        self.assertIn("A02", self.manager.availableShowtimeSeats("S01"))

    def test_showtime_validation_and_ended_movie(self):
        with self.assertRaises(ValueError):
            self.manager.addShowtime(Showtime("S03", "UNKNOWN", "18:30 - 30/10/2026", "R", 1, 2, 1))
        with self.assertRaises(ValueError):
            Showtime("S03", "M00001", "99:99 - 30/10/2026", "R", 1, 2, 1)
        self.manager.movies["M00001"].status = "Ended"
        with self.assertRaises(ValueError):
            self.manager.bookSeats("S01", ["A01"])

    def test_save_load_and_reject_corrupt_showtime_ticket(self):
        self.manager.bookSeats("S01", ["A01", "A02"])
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "shows.json"
            self.manager.saveData(path)
            restored = CinemaManager()
            restored.loadData(path)
            self.assertEqual(restored.to_dict(), self.manager.to_dict())
            import json
            data = self.manager.to_dict()
            data["tickets"][0]["seat_number"] = "Z99"
            path.write_text(json.dumps(data), encoding="utf-8")
            before = restored.to_dict()
            with self.assertRaises(ValueError):
                restored.loadData(path)
            self.assertEqual(restored.to_dict(), before)

    def test_customer_console_books_two_seats(self):
        from Console_io import ConsoleIO
        inputs = ["13", "M00001", "1", "4", "M00001", "1", "A01,A02", "0"]
        output = StringIO()
        with patch("Main.CinemaManager", return_value=self.manager), \
                patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            main()
            ConsoleIO().display_seats("S01", self.manager)
        text = output.getvalue()
        self.assertIn("18:30 - 30/10/2026", text)
        self.assertIn("150,000 VND", text)
        self.assertIn("[X]", text)
        self.assertEqual(len(self.manager.tickets), 2)

    def test_load_old_file_without_showtimes(self):
        import json
        data = {"movies": [sample_movie().to_dict()], "tickets": []}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "old.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.manager.loadData(path)
        self.assertEqual(self.manager.showtimes, {})
        self.assertEqual(self.manager.availableSeats("M00001"), 2)

    def test_full_showtime_and_checked_in_seat(self):
        tickets = self.manager.bookSeats("S01", ["A01", "A02", "A03", "B01", "B02", "B03"])
        self.manager.updateTicket(tickets[0].ticket_id, status="Checked-In")
        self.assertEqual(self.manager.availableShowtimeSeats("S01"), [])
        before = self.manager.to_dict()
        with self.assertRaises(ValueError):
            self.manager.bookSeats("S01", ["A01"])
        self.assertEqual(self.manager.to_dict(), before)

    def test_console_add_movie_showtime_book_and_save(self):
        inputs = [
            "1", "M01", "Movie A", "Comedy", "100", "2026", "75000", "Showing",
            "18:30 - 30/10/2026", "Room 1", "2", "3",
            "12", "M01", "20:30 - 30/10/2026", "Room 1", "2", "3", "80000",
            "4", "M01", "2", "A01,A02", "9", "0",
        ]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "cinema.json"
            output = StringIO()
            with patch("Main.DATA_FILE", path), patch("builtins.input", side_effect=inputs), \
                    redirect_stdout(output):
                main()
            restored = CinemaManager()
            restored.loadData(path)
        self.assertEqual(len(restored.tickets), 2)
        self.assertEqual(len(restored.listShowtimes("M01")), 2)
        self.assertEqual(restored.displayMonthlyRevenue(), [("M01", 160000)])
        self.assertIn("160,000 VND", output.getvalue())

    def test_add_movie_includes_first_showtime_in_menu_13(self):
        manager = CinemaManager()
        output = StringIO()
        inputs = ["1", "M02", "New Movie", "Comedy", "100", "2026", "75000", "Showing",
                  "18:30 - 30/10/2026", "Room 2", "2", "3", "13", "M02", "1", "0"]
        with patch("Main.CinemaManager", return_value=manager), \
                patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            main()
        self.assertEqual(len(manager.listShowtimes("M02")), 1)
        self.assertIn("New Movie | 18:30", output.getvalue())
        self.assertIn("Available: 6/6", output.getvalue())

    def test_invalid_first_showtime_does_not_leave_movie_without_schedule(self):
        manager = CinemaManager()
        inputs = ["1", "M02", "New Movie", "Comedy", "100", "2026", "75000", "Showing",
                  "invalid time", "Room 2", "2", "3", "0"]
        with patch("Main.CinemaManager", return_value=manager), \
                patch("builtins.input", side_effect=inputs), redirect_stdout(StringIO()):
            main()
        self.assertEqual(manager.movies, {})
        self.assertEqual(manager.showtimes, {})

    def test_delete_movie_removes_all_its_showtimes(self):
        self.manager.addMovie(sample_movie("MOTHER"))
        self.manager.addShowtime(Showtime("OTHER", "MOTHER", "18:30 - 30/10/2026", "R2", 1, 2, 1))
        with patch("Main.CinemaManager", return_value=self.manager), \
                patch("builtins.input", side_effect=["3", "M00001", "0"]), \
                redirect_stdout(StringIO()):
            main()
        self.assertNotIn("M00001", self.manager.movies)
        self.assertEqual(list(self.manager.showtimes), ["OTHER"])

    def test_invalid_or_cancelled_time_selection_does_not_delete(self):
        for number in ("0", "99"):
            with self.subTest(number=number):
                before = self.manager.to_dict()
                with patch("Main.CinemaManager", return_value=self.manager), \
                        patch("builtins.input", side_effect=["14", "M00001", number, "0"]), \
                        redirect_stdout(StringIO()):
                    main()
                self.assertEqual(self.manager.to_dict(), before)

    def test_deleted_last_showtime_is_not_displayed_as_legacy_time(self):
        from Console_io import ConsoleIO
        self.manager.deleteShowtime("S01")
        self.manager.deleteShowtime("S02")
        output = StringIO()
        with redirect_stdout(output):
            ConsoleIO().display_movies(list(self.manager.movies.values()), self.manager)
        self.assertIn("No showtimes", output.getvalue())
        self.assertNotIn("19:00 - 25/10/2026", output.getvalue())


class StartupTests(unittest.TestCase):
    def test_startup_loads_movies_showtimes_and_tickets_without_option_10(self):
        saved = CinemaManager()
        saved.addMovie(sample_movie())
        saved.addShowtime(Showtime("S01", "M00001", "18:30 - 30/10/2026", "Room 1", 2, 3, 75000))
        saved.bookSeats("S01", ["A01"])
        loaded = CinemaManager()
        output = StringIO()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "cinema_data.txt"
            saved.saveData(path)
            before = path.read_bytes()
            with patch("Main.DATA_FILE", path), patch("Main.CinemaManager", return_value=loaded), \
                    patch("builtins.input", side_effect=["13", "M00001", "1", "0"]), \
                    redirect_stdout(output):
                main()
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(loaded.to_dict(), saved.to_dict())
        self.assertIn("Automatically loaded", output.getvalue())
        self.assertIn("Available: 5/6", output.getvalue())

    def test_missing_startup_file_still_opens_menu(self):
        output = StringIO()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "missing.txt"
            with patch("Main.DATA_FILE", path), patch("builtins.input", side_effect=["0"]), \
                    redirect_stdout(output):
                main()
            self.assertFalse(path.exists())
        self.assertIn("No saved data file", output.getvalue())
        self.assertIn("Goodbye", output.getvalue())

    def test_invalid_startup_file_reports_error_without_overwriting_file(self):
        for content in (b"invalid JSON", b'{"movies": [], "tickets": "invalid"}', b"\xff"):
            with self.subTest(content=content), tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
                path = Path(directory) / "cinema_data.txt"
                path.write_bytes(content)
                output = StringIO()
                with patch("Main.DATA_FILE", path), patch("builtins.input", side_effect=["0"]), \
                        redirect_stdout(output):
                    main()
                self.assertEqual(path.read_bytes(), content)
                self.assertIn("Could not load saved data", output.getvalue())
                self.assertIn("Goodbye", output.getvalue())


if __name__ == "__main__":
    unittest.main()
