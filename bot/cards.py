"""Card builder helpers."""

from botbuilder.schema import ActionTypes, Attachment, CardAction, CardImage, HeroCard


def build_hero_card() -> Attachment:
    """Build a Hero Card example."""
    card = HeroCard(
        title="Hero Card Demo",
        subtitle="Subtitle",
        text="A Hero Card can contain images, a title, description text, and buttons — ideal for showcasing a single item.",
        images=[CardImage(url="https://aka.ms/bf-welcome-card-image")],
        buttons=[
            CardAction(title="Learn more", type=ActionTypes.open_url, value="https://learn.microsoft.com/azure/bot-service/"),
            CardAction(title="Reply to me", type=ActionTypes.im_back, value="Hello"),
        ],
    )
    return Attachment(content_type="application/vnd.microsoft.card.hero", content=card)


def build_adaptive_card() -> Attachment:
    """Build an Adaptive Card example."""
    card_content = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "size": "Large", "weight": "Bolder", "text": "Adaptive Card Demo"},
            {"type": "TextBlock", "text": "Adaptive Cards 以 JSON 定義，支援文字、圖片與輸入欄位等豐富元件。", "wrap": True},
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Framework", "value": "Bot Framework"},
                    {"title": "Language", "value": "Python"},
                    {"title": "Protocol", "value": "Adaptive Cards v1.5"},
                ],
            },
        ],
        "actions": [
            {"type": "Action.OpenUrl", "title": "Adaptive Cards 官網", "url": "https://adaptivecards.io"},
        ],
    }
    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_content)
