-- ALTER TABLE events ADD COLUMN user_id INTEGER;

-- CREATE TABLE IF NOT EXISTS bookings (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     event_id INTEGER,
--     user_id INTEGER,
--     seats_booked INTEGER,
--     FOREIGN KEY (event_id) REFERENCES events(id),
--     FOREIGN KEY (user_id) REFERENCES users(id)
-- );

-- CREATE TABLE IF NOT EXISTS seats (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     event_id INTEGER,
--     seat_label TEXT,   -- مثل A1, A2, B5
--     is_booked INTEGER DEFAULT 0,
--     user_id INTEGER,
--     FOREIGN KEY (event_id) REFERENCES events(id),
--     FOREIGN KEY (user_id) REFERENCES users(id)
-- );


CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    user_id INTEGER,
    seats_booked INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    seat_label TEXT,   -- مثل A1, A2, B5
    is_booked INTEGER DEFAULT 0,
    user_id INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            seats INTEGER NOT NULL,
            booked INTEGER DEFAULT 0
        , user_id INTEGER);

SELECT * FROM sqlite_master WHERE type='table';
SELECT * FROM sqlite_sequence;
SELECT * FROM users;
SELECT * FROM events;
SELECT * FROM bookings;
SELECT * FROM seats;

DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS sqlite_sequence;
DROP TABLE IF EXISTS users;
