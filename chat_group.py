"""
chat_group.py - Group management for chat system
Handles user groups, connections, and room management
"""

class Group:
    """Manages chat groups and user connections"""
    
    def __init__(self):
        """Initialize group manager"""
        # Dictionary: {username: group_id}
        # group_id = 0 means not in any group (logged in but not chatting)
        self.users = {}
        
        # Dictionary: {group_id: [list of usernames]}
        self.groups = {}
        
        # Counter for creating unique group IDs
        self.group_counter = 1
    
    def join(self, name):
        """
        Add a user to the system (login)
        
        Args:
            name: Username
        """
        if name not in self.users:
            self.users[name] = 0  # 0 = logged in, no group
    
    def leave(self, name):
        """
        Remove a user from the system (logout)
        
        Args:
            name: Username
        """
        if name in self.users:
            # First disconnect from any group
            self.disconnect(name)
            # Then remove from users
            del self.users[name]
    
    def is_member(self, name):
        """
        Check if user is logged in
        
        Args:
            name: Username
            
        Returns:
            True if user exists, False otherwise
        """
        return name in self.users
    
    def connect(self, name1, name2):
        """
        Connect two users in a private chat
        
        Args:
            name1: First user
            name2: Second user
        """
        # If either user is already in a group, disconnect them first
        if self.users.get(name1, 0) != 0:
            self.disconnect(name1)
        if self.users.get(name2, 0) != 0:
            self.disconnect(name2)
        
        # Create new group
        group_id = self.group_counter
        self.group_counter += 1
        
        # Assign both users to this group
        self.users[name1] = group_id
        self.users[name2] = group_id
        
        # Create group member list
        self.groups[group_id] = [name1, name2]
    
    def disconnect(self, name):
        """
        Disconnect a user from their current group
        
        Args:
            name: Username
        """
        if name not in self.users:
            return
        
        group_id = self.users[name]
        
        if group_id == 0:
            # Not in any group
            return
        
        # Remove user from group
        self.users[name] = 0
        
        if group_id in self.groups:
            # Remove from group member list
            if name in self.groups[group_id]:
                self.groups[group_id].remove(name)
            
            # If group is empty, delete it
            if len(self.groups[group_id]) == 0:
                del self.groups[group_id]
            else:
                # Disconnect remaining members too (since it's a private chat)
                for member in self.groups[group_id]:
                    self.users[member] = 0
                del self.groups[group_id]
    
    def list_me(self, name):
        """
        List all members in the same group as the user
        
        Args:
            name: Username
            
        Returns:
            List of usernames in the same group (including the user)
        """
        if name not in self.users:
            return []
        
        group_id = self.users[name]
        
        if group_id == 0:
            # Not in any group
            return [name]
        
        if group_id in self.groups:
            return self.groups[group_id].copy()
        
        return [name]
    
    def list_all(self, name):
        """
        List all users and groups (for debugging/admin)
        
        Args:
            name: Username requesting the list
            
        Returns:
            Formatted string with users and groups
        """
        result = "Users: ------------\n"
        result += str(self.users) + "\n"
        result += "Groups: -----------\n"
        result += str(self.groups) + "\n"
        return result
    
    def get_online_users(self):
        """
        Get list of all online users
        
        Returns:
            List of usernames
        """
        return list(self.users.keys())
    
    def get_group_id(self, name):
        """
        Get the group ID for a user
        
        Args:
            name: Username
            
        Returns:
            Group ID (0 if not in a group)
        """
        return self.users.get(name, 0)