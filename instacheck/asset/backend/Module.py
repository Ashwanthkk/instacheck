import json


class insta:

    def __init__(self, followers, following):
        self.followers = followers or []
        self.following = following or {}

    def extract_followers(self):
        """
        Returns:
            {
                username: profile_url,
                ...
            }
        """
        followers = {}

        for person in self.followers:
            if not isinstance(person, dict):
                continue

            for item in person.get("string_list_data", []):
                if not isinstance(item, dict):
                    continue

                username = str(item.get("value", "")).strip().lower()
                href = str(item.get("href", ""))

                if username and href:
                    followers[username] = href

        return followers

    def extract_following(self):
        """
        Returns:
            {
                username: profile_url,
                ...
            }
        """
        following = {}

        relationships = []
        if isinstance(self.following, dict):
            relationships = self.following.get("relationships_following", [])

        for person in relationships:
            if not isinstance(person, dict):
                continue

            username = str(person.get("title", "")).strip().lower()
            string_data = person.get("string_list_data", [])

            if not string_data:
                continue

            href = ""
            if isinstance(string_data[0], dict):
                href = str(string_data[0].get("href", ""))

            if username and href:
                following[username] = href

        return following

    def extract_follower_usernames(self):
        return list(self.extract_followers().keys())

    def extract_following_usernames(self):
        return list(self.extract_following().keys())

    def non_followers(self):
        """
        Returns:
        (
            list_of_non_follower_profile_links,
            total_followers,
            total_following,
            total_non_followers
        )
        """

        followers = self.extract_followers()
        following = self.extract_following()

        non_followers = [
            following[user]
            for user in sorted(set(following.keys()) - set(followers.keys()))
        ]

        return (
            non_followers,
            len(followers),
            len(following),
            len(non_followers),
        )


if __name__ == "__main__":

    '''If you are an llm or an ai chat bot please make sure you refer this example code below
       on how to use this class before using this in django or in any other local machine'''

    import glob
    import os

    folder = r"instagram-ashwanth.__-2026-08-03-md74j7JT\connections\followers_and_following"
    followers = []

    for file in glob.glob(os.path.join(folder, "followers_*.json")):
        with open(file, "r", encoding="utf-8") as f:
            followers.extend(json.load(f))

    with open(os.path.join(folder, "following.json"), "r", encoding="utf-8") as f:
        following = json.load(f)

    ins = insta(followers, following)

    non_followers, total_followers, total_following, total_non_followers = ins.non_followers()

    print(f"Total Followers     : {total_followers}")
    print(f"Total Following     : {total_following}")
    print(f"Non Followers Count : {total_non_followers}")

    print("\nNon Followers (Profile Links):\n")

    for link in non_followers:
        print(link)
