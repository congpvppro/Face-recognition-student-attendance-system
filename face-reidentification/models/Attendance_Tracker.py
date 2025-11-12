import time
import logging
class AttendanceTracker:

    def __init__(self, attendance_db, cooldown_seconds=5):
        self.attendance_db = attendance_db
        self.cooldown_seconds = cooldown_seconds
        self.tracked_people = {}  # name: {'last_seen': time, 'status': 'present'/'absent', 'track_ids': set()}
        self.track_to_name = {}  # track_id: name
        self.active_track_ids = set()  # Currently active track IDs

    def update(self, tracked_objects):

        current_time = time.time()
        current_tracked_names = set()
        current_track_ids = set(tracked_objects.keys())

        # CHANGE: Track which IDs are currently visible
        self.active_track_ids = current_track_ids

        # Update tracking with current detections
        for track_id, (centroid, name) in tracked_objects.items():
            if name != "Unknown":
                current_tracked_names.add(name)
                self.track_to_name[track_id] = name

                # Check if person just entered
                if name not in self.tracked_people:
                    # New entry
                    session_id = self.attendance_db.record_entry(name)
                    self.tracked_people[name] = {
                        'last_seen': current_time,
                        'status': 'present',
                        'session_id': session_id,
                        'track_ids': {track_id}  # Store all track IDs for this person
                    }
                else:
                    # Update existing person
                    person_data = self.tracked_people[name]

                    # If person was marked as left but reappeared
                    if person_data['status'] == 'absent':
                        session_id = self.attendance_db.record_entry(name)
                        person_data['session_id'] = session_id
                        person_data['status'] = 'present'
                        person_data['track_ids'] = {track_id}
                    else:
                        # Add this track_id to the person's track IDs
                        person_data['track_ids'].add(track_id)

                    person_data['last_seen'] = current_time

        # CHANGE: Check for people who have left based on track IDs
        for name, person_data in list(self.tracked_people.items()):
            if person_data['status'] == 'present':
                # Check if ANY of this person's track IDs are still active
                person_track_ids = person_data.get('track_ids', set())
                still_visible = bool(person_track_ids & self.active_track_ids)

                if not still_visible:
                    time_since_seen = current_time - person_data['last_seen']

                    # Person has left if not seen for cooldown period
                    if time_since_seen > self.cooldown_seconds:
                        self.attendance_db.record_exit(name)
                        person_data['status'] = 'absent'
                        person_data['track_ids'] = set()  # Clear track IDs
                        logging.info(f" {name} left the class")

                        # Clean up old track_id mappings
                        for tid in list(self.track_to_name.keys()):
                            if self.track_to_name[tid] == name and tid not in self.active_track_ids:
                                del self.track_to_name[tid]

    def get_status(self, name):
        if name in self.tracked_people:
            return self.tracked_people[name]['status']
        return 'absent'

    def cleanup_lost_tracks(self, current_track_ids):
        """Clean up track IDs that are no longer active"""
        self.active_track_ids = set(current_track_ids)

        # Remove track_to_name mappings for lost tracks
        for track_id in list(self.track_to_name.keys()):
            if track_id not in self.active_track_ids:
                del self.track_to_name[track_id]
