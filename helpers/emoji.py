from emoji_list import emoji_list

def emoji_name_to_unicode(short_name, start_idx=0, end_idx=(len(emoji_list) - 1)):
    """
    Performs a binary search on emoji_list for an emoji's short_name
    and returns its corresponding unicode string. If short_name is
    not found, None is returned.
    """
    mid_idx = (start_idx + end_idx) // 2
    mid_name = emoji_list[mid_idx].get("short_name")
   
    if short_name == mid_name:
        return emoji_list[mid_idx].get("unicode")
    elif start_idx == end_idx:
        return None
    elif short_name > mid_name:
        return emoji_name_to_unicode(short_name, 
                                     start_idx=mid_idx+1,
                                     end_idx=end_idx
        )
    elif short_name < mid_name:
        return emoji_name_to_unicode(short_name,
                                     start_idx=start_idx,
                                     end_idx=mid_idx-1
        )