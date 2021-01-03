data "archive_file" "source" {
  type        = "zip"
  source_file = "${path.module}/../sync.py"
  output_path = "${path.module}/sync.py.zip"
}

resource "aws_lambda_function" "sync" {
  filename = "${path.module}/sync.py.zip"

  source_code_hash = data.archive_file.source.output_base64sha256
  function_name    = "sync"
  description      = "Polls Strava for new activities, writes to S3"
  runtime          = "python3.8"
  role             = aws_iam_role.sync.arn
  handler          = "sync.lambda_handler"
  timeout          = 30

  environment {
    variables = {
      CLIENT_ID     = var.CLIENT_ID
      CLIENT_SECRET = var.CLIENT_SECRET
    }
  }
}

data "aws_iam_policy_document" "sync" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "logs:PutLogEvents",
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    actions = [
      "dynamodb:*"
    ]

    resources = ["arn:aws:dynamodb:eu-north-1:376590904315:table/strava"]
  }
  statement {
    actions = [
      "s3:*"
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "sync" {
  name_prefix = "sync-"
  policy      = data.aws_iam_policy_document.sync.json
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sync" {
  name               = "sync"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "sync" {
  role       = aws_iam_role.sync.name
  policy_arn = aws_iam_policy.sync.arn
}

resource "aws_cloudwatch_event_rule" "every_five_minute" {
  name                = "every-five-minutes"
  description         = "Fires every fives minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "event_target-sentor" {
  rule      = aws_cloudwatch_event_rule.every_five_minute.name
  target_id = "lambda"
  arn       = aws_lambda_function.sync.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_five_minute.arn
}
