"""
chat_group.py - Enhanced Group Management
Supports both 2-person private chats and 3+ person group chats
"""

class Group:
    """
    Enhanced group management supporting:
    - 2-person private chats
    - 3+ person group chats
    - Message broadcasting to all members
    """
    
    def __init__(self):
        """Initialize group management"""
        # Track all groups: {group_id: [member1, member2, ...]}
        self.groups = {}
        
        # Track user's current group: {username: group_id}
        self.user_to_group = {}
        
        # Track private 2-person chats: {(user1, user2): group_id}
        self.private_chats = {}
        
        # Track all registered users (needed for validation)
        self.users = set()
        
        # Group ID counter
        self.next_group_id = 1
    
    def add_user(self, username):
        """
        Register a new user in the system
        
        Args:
            username: Username to register
        """
        self.users.add(username)
    
    def connect(self, user1, user2):
        """
        Create or join a 2-person private chat (backward compatible)
        
        Args:
            user1: First user
            user2: Second user
            
        Returns:
            group_id or None if failed
        """
        # Check if either user is already in a group
        if user1 in self.user_to_group or user2 in self.user_to_group:
            return None
        
        # Check if private chat already exists
        pair = tuple(sorted([user1, user2]))
        if pair in self.private_chats:
            group_id = self.private_chats[pair]
        else:
            # Create new private chat
            group_id = f"private_{self.next_group_id}"
            self.next_group_id += 1
            self.groups[group_id] = [user1, user2]
            self.private_chats[pair] = group_id
        
        # Add users to group
        self.user_to_group[user1] = group_id
        self.user_to_group[user2] = group_id
        
        return group_id
    
    def create_group(self, members):
        """
        Create a new group chat with 3+ members
        
        Args:
            members: List of usernames [user1, user2, user3, ...]
            
        Returns:
            (success: bool, group_id or error_message)
        """
        # Validate input
        if not members or len(members) < 3:
            return False, "Groups need at least 3 members"
        
        # Check if any member is already in a group
        busy_users = [u for u in members if u in self.user_to_group]
        if busy_users:
            return False, f"Users already in chat: {', '.join(busy_users)}"
        
        # Create new group
        group_id = f"group_{self.next_group_id}"
        self.next_group_id += 1
        
        self.groups[group_id] = list(members)
        
        # Map all members to this group
        for member in members:
            self.user_to_group[member] = group_id
        
        return True, group_id
    
    def get_group_members(self, group_id):
        """
        Get all members in a group
        
        Args:
            group_id: Group ID
            
        Returns:
            List of member usernames
        """
        return self.groups.get(group_id, [])
    
    def get_user_group(self, username):
        """
        Get the group ID that a user is in
        
        Args:
            username: Username to look up
            
        Returns:
            group_id or None
        """
        return self.user_to_group.get(username)
    
    def get_other_members(self, username):
        """
        Get all other members in the user's group
        
        Args:
            username: Username
            
        Returns:
            List of other member usernames (excluding the user)
        """
        group_id = self.user_to_group.get(username)
        if not group_id:
            return []
        
        members = self.groups.get(group_id, [])
        return [m for m in members if m != username]
    
    def disconnect(self, username):
        """
        Remove a user from their group
        
        Args:
            username: User to disconnect
            
        Returns:
            (group_id, remaining_members) or (None, [])
        """
        group_id = self.user_to_group.get(username)
        if not group_id:
            return None, []
        
        # Remove user from group
        if group_id in self.groups:
            self.groups[group_id].remove(username)
            remaining = self.groups[group_id]
            
            # If group is empty, delete it
            if not remaining:
                del self.groups[group_id]
                
                # Clean up private chat mapping if it exists
                for pair, gid in list(self.private_chats.items()):
                    if gid == group_id:
                        del self.private_chats[pair]
            
            # If only 1 person left, disconnect them too
            elif len(remaining) == 1:
                last_user = remaining[0]
                del self.groups[group_id]
                if last_user in self.user_to_group:
                    del self.user_to_group[last_user]
                
                # Clean up private chat mapping
                for pair, gid in list(self.private_chats.items()):
                    if gid == group_id:
                        del self.private_chats[pair]
                
                return group_id, []
        
        # Remove user from mapping
        del self.user_to_group[username]
        
        return group_id, self.groups.get(group_id, [])
    
    def is_in_group(self, username):
        """Check if user is in any group"""
        return username in self.user_to_group
    
    def get_group_info(self, username):
        """
        Get detailed group information for a user
        
        Returns:
            {
                'group_id': str,
                'members': list,
                'is_private': bool,
                'member_count': int
            }
        """
        group_id = self.user_to_group.get(username)
        if not group_id:
            return None
        
        members = self.groups.get(group_id, [])
        
        return {
            'group_id': group_id,
            'members': members,
            'is_private': group_id.startswith('private_'),
            'member_count': len(members)
        }