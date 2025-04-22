import time
from collections import defaultdict

class ItemTracker:
    def __init__(self, time_threshold=5.0):
        """
        Track items detected by the system
        
        Args:
            time_threshold (float): Time in seconds to increment quantity counter
        """
        # Dictionary to store item counts and their last seen timestamps
        self.items = defaultdict(lambda: {
            "count": 0, 
            "last_seen": 0, 
            "continuous_time": 0,
            "last_added_time": 0
        })
        self.time_threshold = time_threshold
    
    def update_items(self, detected_items):
        """
        Update item tracking and counts based on currently detected items
        
        Args:
            detected_items (set): Set of class names detected in current frame
            
        Returns:
            dict: Updated items dictionary
        """
        current_time = time.time()
        
        # Update item tracking and counts
        for cls_name in list(self.items.keys()) + list(detected_items):
            # Initialize if not exists
            if cls_name not in self.items:
                self.items[cls_name] = {
                    "count": 0, 
                    "last_seen": 0, 
                    "continuous_time": 0,
                    "last_added_time": 0
                }
                
            if cls_name in detected_items:
                # Item is currently visible
                if self.items[cls_name]["last_seen"] == 0:
                    # First time seeing this item in this sequence
                    self.items[cls_name]["last_seen"] = current_time
                    self.items[cls_name]["continuous_time"] = 0
                else:
                    # Calculate continuous visibility time
                    elapsed = current_time - self.items[cls_name]["last_seen"]
                    self.items[cls_name]["continuous_time"] += elapsed
                    self.items[cls_name]["last_seen"] = current_time
                    
                    # Check if the cooldown period has elapsed since last adding this item
                    cooldown_elapsed = current_time - self.items[cls_name]["last_added_time"]
                    
                    # If continuously visible for more than threshold AND cooldown has elapsed, increment count
                    if (self.items[cls_name]["continuous_time"] >= self.time_threshold and 
                        (self.items[cls_name]["last_added_time"] == 0 or cooldown_elapsed >= self.time_threshold)):
                        print(f"Adding {cls_name} to bill - visible for {self.items[cls_name]['continuous_time']:.2f} seconds")
                        self.items[cls_name]["count"] += 1
                        self.items[cls_name]["continuous_time"] = 0  # Reset timer after incrementing
                        self.items[cls_name]["last_added_time"] = current_time  # Update last added time
            else:
                # Item is not visible in this frame
                if self.items[cls_name]["last_seen"] > 0:
                    # Item just disappeared
                    elapsed = current_time - self.items[cls_name]["last_seen"]
                    total_visible_time = self.items[cls_name]["continuous_time"] + elapsed
                    
                    # Check cooldown
                    cooldown_elapsed = current_time - self.items[cls_name]["last_added_time"]
                    
                    # If visible for less than threshold but greater than 0 AND cooldown has elapsed, count as 1
                    if (0 < total_visible_time < self.time_threshold and 
                        self.items[cls_name]["continuous_time"] > 0 and
                        (self.items[cls_name]["last_added_time"] == 0 or cooldown_elapsed >= self.time_threshold)):
                        print(f"Adding {cls_name} to bill - disappeared after {total_visible_time:.2f} seconds")
                        self.items[cls_name]["count"] += 1
                        self.items[cls_name]["last_added_time"] = current_time  # Update last added time
                    
                    # Reset tracking for this item
                    self.items[cls_name]["last_seen"] = 0
                    self.items[cls_name]["continuous_time"] = 0
                    
        return self.items
    
    def clear_items(self):
        """Reset all tracked items"""
        self.items.clear()
        
    def get_items(self):
        """Get the current items dictionary"""
        return self.items