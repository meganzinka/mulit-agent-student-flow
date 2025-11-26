"""Profile loader for reading and parsing student YAML files."""

import yaml
from pathlib import Path
from typing import List, Dict
from rehearsed_multi_student.models.schemas import StudentProfile


class ProfileLoader:
    """Loads student profiles from YAML files."""
    
    def __init__(self, profiles_dir: Path | None = None):
        """Initialize the profile loader.
        
        Args:
            profiles_dir: Directory containing profile YAML files.
                         Defaults to the profiles directory in this package.
        """
        if profiles_dir is None:
            # Default to the profiles directory
            self.profiles_dir = Path(__file__).parent
        else:
            self.profiles_dir = Path(profiles_dir)
    
    def load_profile(self, profile_path: Path) -> StudentProfile:
        """Load a single student profile from a YAML file.
        
        Args:
            profile_path: Path to the YAML profile file
            
        Returns:
            StudentProfile object
        """
        with open(profile_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return StudentProfile(**data)
    
    def load_all_profiles(self) -> List[StudentProfile]:
        """Load all student profiles from the profiles directory.
        
        Returns:
            List of StudentProfile objects
        """
        profiles = []
        yaml_files = sorted(self.profiles_dir.glob("*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                profile = self.load_profile(yaml_file)
                profiles.append(profile)
            except Exception as e:
                print(f"Error loading profile {yaml_file}: {e}")
                continue
        
        return profiles
    
    def get_profile_by_id(self, profile_id: str) -> StudentProfile | None:
        """Get a specific profile by ID.
        
        Args:
            profile_id: The ID of the profile to retrieve
            
        Returns:
            StudentProfile if found, None otherwise
        """
        profiles = self.load_all_profiles()
        for profile in profiles:
            if profile.id == profile_id:
                return profile
        return None
    
    def get_profiles_dict(self) -> Dict[str, StudentProfile]:
        """Get all profiles as a dictionary keyed by profile ID.
        
        Returns:
            Dictionary mapping profile IDs to StudentProfile objects
        """
        profiles = self.load_all_profiles()
        return {profile.id: profile for profile in profiles}
