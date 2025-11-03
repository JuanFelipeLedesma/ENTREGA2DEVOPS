from marshmallow import Schema, fields
class BlacklistSchema(Schema):
    id = fields.UUID()
    email = fields.Email()
    app_uuid = fields.UUID()
    blocked_reason = fields.Str(allow_none=True)
    request_ip = fields.Str(allow_none=True)
    created_at = fields.DateTime()
