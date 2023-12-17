import json
import logging
import time

from jsonschema import Draft3Validator  # As of May 2022, st2 enquiry uses Draft3
from errbot import BotFlow, BotPlugin, Command, FlowRoot, botcmd, botflow, re_botcmd

log = logging.getLogger(__name__)

# https://json-schema.org/draft-07/json-schema-validation.html#rfc.section.6.1.1

# String values MUST be one of the six primitive types ("null",
# "boolean", "object", "array", "number", or "string"), or "integer"
# which matches any number with a zero fractional part.

JSON_TYPE = {
    "null": None,
    "boolean": bool,
    "object": dict,
    "array": list,
    "number": float,  # detect '.' use float type otherwise int type.
    "string": str,
}


class EnquiryManager:
    def __init__(self):
        """
        enquiries are stored as:
            user:
                current: enquiry_id
                responses:
                    enquiry_id: enquiry_obj
        """
        self.enquiries = {}

    def get_current_enquiry(self, chat_user):
        """
        Get the current enquiry id for responses or None if not set.
        :chat_user: errbot identifier - the user identification.
        """
        user_id = chat_user.aclattr
        if user_id:
            # errbot objects can't be hashed so use ACL to uniquely identify the chat user.
            return self.enquiries.get(user_id, {}).get("current")

    def get(self, chat_user, enquiry_id):
        """
        :chat_user: Errbot Person object.
        :enquiry_id:
        Get the enquiry object for the user_id enquiry_id pair.
        Returns None if the user_id/enquiry_id are not found.
        """
        if not chat_user or not enquiry_id:
            return None
        
        user_id = chat_user.aclattr
        current = self.enquiries.get(user_id)
        if current:
            enquiry = current["responses"].get(enquiry_id)
            if enquiry:
                return enquiry.next()

    def next(self, chat_user):
        """
        :user_id: Errbot Person object.
        """
        if not char_user:
            return None

        user_id = chat_user.aclattr

        current = self.enquiries.get(user_id, {}).get("current")
        if current:
            return self.get(user_id, current)

    def set(self, chat_user, enquiry_id):
        """
        :user_id: Errbot Person object.
        :enquiry_id: The enquiry id that will be set as active for answers and response submission.
        """
        if not chat_user:
            return False

        # Use unique identification aclattr because Errbot Person object is not hashable.
        user_id = chat_user.aclattr

        if user_id not in self.enquiries:
            self.enquiries[user_id] = {"current": None, "responses": {}}
        self.enquiries[user_id]["current"] = enquiry_id
        return True

    def purge_expired(self):
        purge_list = []
        for user in self.enquiries:
            for enquiry in user["responses"]:
                if self.enquiries[user]["responses"][enquiry].has_expired:
                    purge_list.append([user, enquiry])
        for i in purge_list:
            user, enquiry = i
            del self.enquiries[user]["responses"][enquiry]


class Enquiry:
    def __init__(self, enquiry, ttl=3600):
        """
        The Enquiry class wraps the St2 API response in a Python Object.   The Python object
        tracks the answers provided for the specific enquiry and maintains a time to live for
        answers to be considered abandonned.

        :enquiry: the stackstorm enquiry API response object in JSON form.
        :ttl: time to live before an enquiry expires.
        """
        self.validator = None

        self.enquiry_data = json.loads(enquiry)
        self.answers = {}
        self.expiration = time.time() + ttl

    @classmethod
    def get_associated_data(cls):
        """
        The enquiry data is insufficent to identify its association with a specific workflow.
        The get_associated_data function queries the associated execution_id and then the
        associated workflow to collect descriptions.
        """
        raise NotImplementedError

    @property
    def id(self):
        return self.enquiry_data["id"]

    def next(self):
        """
        next() returns the next question to be answered in an enquiry object.
        """
        
        for k in self.enquiry_data["schema"]["properties"]:
            if k not in self.answers:
                return self.enquiry_data["schema"]["properties"][k].get("description")
        else:
            return "All questions have been answered."

    @property
    def has_expired(self):
        return time.time() > self.expiration

    def response(self, num, answer):
        """
        response: Answer a specific question in the enquiry.
        :num: int the question to be answered (order in the query)
        :answer: any the answer that conforms with the enquiry schema
        """
        if self.answers:
            return "finished"
        else:
            self.answers["a"] = 1
            return "Is this ok?"

    def check_answer(self, num, answer):
        """
        compare the answer data type with the schema
        """
        raise NotImplementedError

    def check_schema(self):
        """
        compare the answer data type with the schema
        """
        self.validator = Draft3Validator(json.loads(enquiry)["schema"])
        try:
            self.validator.check_schema(self.enquiry["schema"])
        except jsonschema.exceptions.SchemaError as err:
            log.exception(err)
            return False
        return True
