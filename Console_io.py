"""Console input and output, following the sample project's separation of roles."""


class ConsoleIO:
    def show_menu(self):
        print("\n============================================")
        print("   MOVIE TICKET PURCHASE MANAGEMENT")
        print("============================================")
        print("1. Add Movie with First Showtime")
        print("2. Search Movie")
        print("3. Delete Movie and Its Showtimes (Movie ID, e.g. M00007)")
        print("4. Book Tickets - Choose Showtime and Seats")
        print("5. Update Ticket")
        print("6. Highest Selling Movies")
        print("7. Ticket Sales")
        print("8. Monthly Revenue")
        print("9. Save Data to File")
        print("10. Reload Data from File")
        print("11. Test File I/O")
        print("12. Add Another Showtime by Movie ID (staff)")
        print("13. View Showtimes and Available Seats (customer)")
        print("14. Delete One Showtime - Movie ID, then Choose Time")
        print("0. Exit")
        print("--------------------------------------------")

    def read_string(self, prompt):
        return input(prompt).strip()

    def read_int(self, prompt):
        while True:
            try:
                value = int(input(prompt))
                if value >= 0:
                    return value
            except ValueError:
                pass
            print("Please enter a non-negative whole number.")

    def display_movies(self, movies, manager):
        if not movies:
            print("No movies found.")
        for movie in movies:
            print(f"{movie.movie_id} | {movie.title} | {movie.genre} | "
                  f"{movie.duration_minutes} minutes | {movie.status}")
            shows = manager.listShowtimes(movie.movie_id)
            if shows:
                self.display_showtimes(shows, manager)
            else:
                print("  No showtimes yet. Use option 12 to add one.")

    def display_showtimes(self, showtimes, manager):
        if not showtimes:
            print("No showtimes found.")
            return
        print("\nMOVIE ID | MOVIE | START | ROOM | PRICE | AVAILABLE | STATUS")
        for show in showtimes:
            movie = manager.movies[show.movie_id]
            count = len(manager.availableShowtimeSeats(show.showtime_id))
            total = show.rows * show.seats_per_row
            print(f"{movie.movie_id} | {movie.title} | {show.starts_at} | "
                  f"{show.room} | {show.ticket_price:,} VND | {count}/{total} | {movie.status}")

    def choose_showtime(self, manager):
        """Dùng chung một cách chọn cho xem ghế, đặt vé và xóa suất."""
        self.display_movies(list(manager.movies.values()), manager)
        if not manager.movies:
            return None
        movie_id = self.read_string("Movie ID (e.g. M00007; blank to go back): ")
        if not movie_id:
            return None
        if movie_id not in manager.movies:
            if movie_id in manager.showtimes:
                correct_id = manager.showtimes[movie_id].movie_id
                raise ValueError(f"Please use Movie ID {correct_id}, then choose the time")
            raise ValueError("Movie not found")
        shows = manager.listShowtimes(movie_id)
        if not shows:
            print("This movie has no showtimes. Use option 12 to add one.")
            return None
        for number, show in enumerate(shows, start=1):
            print(f"{number}. {show.starts_at} | {show.room} | {show.ticket_price:,} VND")
        number = self.read_int("Choose time number (0 to go back): ")
        if number == 0:
            return None
        if not 1 <= number <= len(shows):
            raise ValueError("Invalid time number")
        return shows[number - 1]

    def display_seats(self, showtime_id, manager):
        available = set(manager.availableShowtimeSeats(showtime_id))
        show = manager.showtimes[showtime_id]
        movie = manager.movies[show.movie_id]
        print(f"\n{movie.title} | {show.starts_at} | {show.room}")
        print(f"Price per seat: {show.ticket_price:,} VND")
        print("SCREEN - [A01] = available, [X] = booked")
        seats = show.seat_numbers()
        for start in range(0, len(seats), show.seats_per_row):
            row = seats[start:start + show.seats_per_row]
            print(" ".join(f"[{seat}]" if seat in available else "[X]" for seat in row))
        print(f"Available: {len(available)}/{len(seats)}")

    def display_totals(self, rows, manager, unit):
        if not rows:
            print("No results.")
        for movie_id, total in rows:
            print(f"{movie_id} | {manager.movies[movie_id].title}: {total:,} {unit}")
