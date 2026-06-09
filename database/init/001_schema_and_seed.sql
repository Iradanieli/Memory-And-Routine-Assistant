CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    related_person TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Scheduled'
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'Open'
);

INSERT INTO events (
    event_id, title, date, time, location, related_person, notes, status
) VALUES
    ('E001', 'Appointment with Dr. Amir Cohen', '2025-06-10', '09:30', 'GreenCare Clinic', 'Dana', 'Bring ID card and medication list', 'Scheduled'),
    ('E002', 'Walk with Ruth', '2025-06-10', '17:00', 'Neighborhood park', 'Ruth', 'Meet near the building entrance and wear comfortable shoes', 'Scheduled'),
    ('E004', 'Maya evening call', '2025-06-10', '19:00', 'Phone', 'Maya', 'Maya usually calls in the evening', 'Scheduled'),
    ('E003', 'Family dinner with Daniel', '2025-06-13', '18:30', 'Daniel''s home', 'Daniel', 'Dana will arrange transportation', 'Scheduled'),
    ('E005', 'Video call with Daniel', '2026-05-31', '17:30', 'Living room', 'Daniel', 'Dana will help start the call if needed', 'Scheduled'),
    ('E006', 'Family lunch with Maya', '2026-06-02', '13:00', 'Maya''s home', 'Maya', 'Bring a light jacket', 'Scheduled'),
    ('E12D63E62', 'Walking at the shore', '2026-06-03', '18:00', 'Herzliya', 'Dana', 'Bring walking shoes', 'Scheduled'),
    ('E45CBD63F', 'NBA game', '2026-06-06', '23:00', 'My home', '', '', 'Scheduled'),
    ('EE765AC55', 'Video call with Aviv', '2026-06-08', '20:00', 'My home', 'Aviv', '', 'Scheduled'),
    ('E008', 'Walk in the neighborhood park', '2026-06-09', '16:45', 'Neighborhood park', 'Ruth', 'Meet near the building entrance', 'Scheduled'),
    ('EC353B52A', 'Space Lecture', '2026-06-10', '18:00', 'Ramat Gan Conference Hall', 'Daniel', 'Dress nicely', 'Scheduled'),
    ('E193E3CBB', 'Watching Basketball game on TV', '2026-06-10', '20:50', 'My home', 'Daniel', '', 'Scheduled'),
    ('E0B33A86F', 'Watching World Cup Opening Game', '2026-06-11', '22:00', 'My home', 'Daniel', 'EL EL ISRAEL', 'Scheduled'),
    ('E09', 'Phone call with Rachel', '2026-06-12', '19:00', 'Phone', 'Rachel', 'Call after dinner', 'Scheduled'),
    ('E010', 'Pharmacy pickup', '2026-06-18', '11:00', 'Central Pharmacy', 'Dana', 'Pick up renewed prescription', 'Scheduled'),
    ('E011', 'Family dinner with Daniel', '2026-06-26', '18:30', 'Daniel''s home', 'Daniel', 'Dana will arrange transportation', 'Scheduled')
ON CONFLICT (event_id) DO NOTHING;

INSERT INTO tasks (
    task_id, title, date, time, priority, status
) VALUES
    ('T001', 'Bring medication list to clinic appointment', '2026-05-28', '08:30', 'High', 'Open'),
    ('T002', 'Call Daniel if confused about transportation', '2026-05-28', '08:45', 'High', 'Open'),
    ('T003', 'Take morning medication', '2026-05-31', '08:00', 'High', 'Closed'),
    ('T004', 'Prepare phone for Daniel''s video call', '2026-05-31', '17:00', 'Medium', 'Open'),
    ('T005', 'Take morning medication', '2026-06-01', '08:00', 'High', 'Closed'),
    ('T006', 'Take morning medication', '2026-06-02', '08:00', 'High', 'Closed'),
    ('T007', 'Take morning medication', '2026-06-03', '08:00', 'High', 'Open'),
    ('T008', 'Take morning medication', '2026-06-04', '08:00', 'High', 'Closed'),
    ('T009', 'Take morning medication', '2026-06-05', '08:00', 'High', 'Open'),
    ('T010', 'Put medication list in the bag', '2026-06-05', '08:30', 'High', 'Open'),
    ('T011', 'Bring ID card to clinic appointment', '2026-06-05', '08:35', 'High', 'Open'),
    ('T012', 'Call Dana before leaving for the clinic', '2026-06-05', '09:15', 'High', 'Open'),
    ('T013', 'Take morning medication', '2026-06-06', '08:00', 'High', 'Closed'),
    ('T014', 'Take morning medication', '2026-06-07', '08:00', 'High', 'Open'),
    ('T015', 'Take morning medication', '2026-06-08', '08:00', 'High', 'Open'),
    ('T016', 'Take morning medication', '2026-06-09', '08:00', 'High', 'Open'),
    ('T017', 'Take morning medication', '2026-06-10', '08:00', 'High', 'Open'),
    ('T018', 'Take morning medication', '2026-06-11', '08:00', 'High', 'Open'),
    ('T019', 'Take morning medication', '2026-06-12', '08:00', 'High', 'Open'),
    ('T020', 'Take morning medication', '2026-06-13', '08:00', 'High', 'Open'),
    ('T021', 'Check pharmacy note on kitchen table', '2026-06-18', '09:30', 'Medium', 'Open')
ON CONFLICT (task_id) DO NOTHING;
