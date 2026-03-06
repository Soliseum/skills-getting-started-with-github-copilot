"""
API endpoint tests for the Mergington High School Activities API.

All tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and prepare request parameters
- Act: Execute the API call via TestClient
- Assert: Verify response status, body, and state changes
"""

from src.app import activities


class TestRootEndpoint:
    """Tests for the root endpoint (/)"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that the root endpoint redirects to /static/index.html"""
        # Arrange
        expected_redirect = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_success(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity contains all required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, activity_data in data.items():
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        assert email in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count + 1
    
    def test_signup_for_activity_duplicate_error(self, client):
        """Test that signing up twice for the same activity returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
        assert len(activities[activity]["participants"]) == initial_count  # No change
    
    def test_signup_for_nonexistent_activity_error(self, client):
        """Test that signing up for a non-existent activity returns 404 error"""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup works with URL-encoded activity names"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Math Olympiad"  # Contains space
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant from an activity"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity}"
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count - 1
    
    def test_remove_nonexistent_participant_error(self, client):
        """Test that removing a non-existent participant returns 404 error"""
        # Arrange
        email = "nonexistent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found in this activity"
    
    def test_remove_participant_from_nonexistent_activity_error(self, client):
        """Test that removing participant from non-existent activity returns 404 error"""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_remove_participant_with_special_characters(self, client):
        """Test removal works with URL-encoded names and emails"""
        # Arrange
        email = "ethan@mergington.edu"  # In Math Olympiad
        activity = "Math Olympiad"  # Contains space
        
        # Act
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # Assert
        assert response.status_code == 200
        assert email not in activities[activity]["participants"]


class TestEndToEndWorkflow:
    """Integration tests for complete workflows"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test the complete workflow of signing up and removing a participant"""
        # Arrange
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Act & Assert - Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Act & Assert - Remove
        remove_response = client.delete(f"/activities/{activity}/participants/{email}")
        assert remove_response.status_code == 200
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_for_different_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        # Arrange
        email = "multisport@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Club"]
        
        # Act
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            
            # Assert
            assert response.status_code == 200
            assert email in activities[activity]["participants"]
