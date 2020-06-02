"""
   Copyright 2020 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.​

    This sample generates an arcade expression based on a CSV file of user-names, full names, or categories.
"""
import argparse
import csv
import textwrap


def main(args):
    expression = ""
    with open(args.file) as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for i, row in enumerate(reader):
            if i == 0:
                expression += textwrap.dedent(f"""
                if ($feature.created_user == '{row[args.username_column].strip()}') {{
                    return '{row[args.other_column].strip()}'
                }}
                """)
            else:
                expression += textwrap.dedent(f"""
                else if ($feature.created_user == '{row[args.username_column].strip()}') {{
                    return '{row[args.other_column].strip()}'
                }}
                """)
        expression += textwrap.dedent(f"""
        return ''
        """)
    print(expression)


if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Generates an Arcade expression using a CSV file.")
    parser.add_argument('--file', '-f', dest='file', help="The file to open", required=True)
    parser.add_argument('--username-column', dest='username_column', help="The name of the column containing the usernames", default="username")
    parser.add_argument('--other-column', dest='other_column', help="The name of the other column containing the names, categories, or other strings.", default="category")
    args = parser.parse_args()
    main(args)