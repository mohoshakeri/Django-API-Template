from typing import Any, Optional, Tuple, Union

from project_title.log import logger_set

logger = logger_set("services.sms")


class SMS:
    client: Any = None
    message: Optional[str] = None
    pattern: Optional[str]

    def __init__(self, sms_name: Optional[str] = None) -> None:
        self.kwargs: dict = {}
        self.pattern = sms_name
        self.client = None  # Todo -> Add Client

    def ready(self, **kwargs: Any) -> "SMS":
        if self.pattern:
            with open("templates/sms/{}.temp".format(self.pattern), "r") as f:
                template: str = f.read()
            self.message = template.format(**kwargs)
            self.kwargs = kwargs
            return self

        # Direct text message without pattern
        self.message = kwargs.get("message")
        return self

    def send(self, mobile: str) -> Tuple[str, Optional[Any]]:
        if self.message is None:
            raise ValueError("Message cannot be None")

        # Skip actual SMS in development environment
        if True:  # Todo ->  Production
            message_id: str = "xxxxxxxTESTxxxxxxxx"
            return message_id, None

        send_req = self.client.send_sms(mobile, self.message).json()
        if (
            "data" in send_req
            and isinstance(send_req["data"], dict)
            and "messageIds" in send_req["data"]
            and isinstance(send_req["data"]["messageIds"], list)
            and len(send_req["data"]["messageIds"]) > 0
        ):
            message_id = str(send_req["data"].get("messageIds")[0])
            return message_id, None

        logger.info(msg={"message": "SMS API Error", "response": send_req})
        raise ValueError("SMS API returned invalid data")

    def is_delivered(self, message_id: Union[str, int]) -> Optional[bool]:
        deliver_check_request = self.client.report_message(message_id).json()

        # Delivered
        if (
            "data" in deliver_check_request
            and "deliveryState" in deliver_check_request["data"]
            and str(deliver_check_request["data"]["deliveryState"]) in ["1", "2", "3"]
        ):
            return True

        # Not Delivered
        if (
            "data" in deliver_check_request
            and "deliveryState" in deliver_check_request["data"]
            and str(deliver_check_request["data"]["deliveryState"]) in ["6", "7", "4"]
        ):
            return False

        # Running
        return None
