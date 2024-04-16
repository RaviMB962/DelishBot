
import re

def extract_session_id(session_str: str):

    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match :
        extracted_string = match.group(1)
        return extracted_string

    return ""


def get_string_from_food_dictionary(food_dict: dict):
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])

#if __name__ == "__main__":
    #print(extract_session_id("projects/delishbot-hktw/agent/sessions/74e82817-fe87-7992-0ee7-5f8097f92b25/contexts/ongoing-order"))
    #print(get_string_from_food_dictionary({"samosa":2, "chhole":5}))