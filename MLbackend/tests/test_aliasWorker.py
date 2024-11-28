import unittest
from unittest.mock import MagicMock, patch, mock_open
from typing import List
import git
import yaml
import os
from MLbackend.src.alias_worker import replace_aliases


class MockConfiguration:
    def __init__(self, repositoryPath):
        self.repositoryPath = repositoryPath

class MockLogger:
    def info(self, msg):
        print(msg)

class MockCommit:
    def __init__(self, author_email):
        self.author = MagicMock()
        self.author.email = author_email


class TestReplaceAliases(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MockLogger()
        self.mock_config = MockConfiguration(repositoryPath="/test/repo")

    @patch("builtins.open", new_callable=mock_open, read_data="alias1:\n  - email1@example.com\n  - email2@example.com\n")
    @patch("os.path.exists", return_value=True)
    def test_alias_replacement(self, mock_exists, mock_open):
        commits = [
            MockCommit(author_email="email1@example.com"),
            MockCommit(author_email="email2@example.com"),
            MockCommit(author_email="other@example.com"),
        ]

        expected_emails = ["alias1", "alias1", "other@example.com"]
        result = list(replace_aliases(commits, self.mock_config, self.mock_logger))
        actual_emails = [commit.author.email for commit in result]

        self.assertEqual(actual_emails, expected_emails)

    @patch("os.path.exists", return_value=False)
    def test_no_alias_file(self, mock_exists):
        commits = [MockCommit(author_email="email1@example.com")]
        result = list(replace_aliases(commits, self.mock_config, self.mock_logger))
        actual_emails = [commit.author.email for commit in result]

        self.assertEqual(actual_emails, ["email1@example.com"])

    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("os.path.exists", return_value=True)
    def test_empty_alias_file(self, mock_exists, mock_open):
        commits = [MockCommit(author_email="email1@example.com")]
        result = list(replace_aliases(commits, self.mock_config, self.mock_logger))
        actual_emails = [commit.author.email for commit in result]

        self.assertEqual(actual_emails, ["email1@example.com"])

    def test_empty_commits_list(self):
        result = list(replace_aliases([], self.mock_config, self.mock_logger))
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
