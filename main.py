import json
from pathlib import Path
from sys import stderr

from parser.pg_parser import ParserPG, ParsingPGError
from plan_gen.exec_instr import ExecInstrTracker
from plan_gen.plan_generator import PlanGenerator

SCRIPT_DIR = Path(__file__).parent.absolute()
Path(f"{SCRIPT_DIR}/queries").mkdir(exist_ok=True)
Path(f"{SCRIPT_DIR}/out").mkdir(exist_ok=True)
Path(f"{SCRIPT_DIR}/out/O1").mkdir(exist_ok=True)
Path(f"{SCRIPT_DIR}/out/O3").mkdir(exist_ok=True)
Path(f"{SCRIPT_DIR}/out/Tracker").mkdir(exist_ok=True)


def plan_gen(parser: ParserPG, src_filename: str):
    generator = PlanGenerator(parser)
    generator.generate_optimal_plan(O3=False)
    generator.dump_plan_to_json_file(f"{SCRIPT_DIR}/out/O1/{src_filename}.json")


def plan_gen_o3(parser: ParserPG, src_filename: str):
    generator = PlanGenerator(parser)
    generator.generate_optimal_plan(O3=True)
    generator.dump_plan_to_json_file(f"{SCRIPT_DIR}/out/O3/{src_filename}.json")


def dump_exec_instr_tracker():
    received = ExecInstrTracker.get_statistic_info()
    json_str = json.dumps(received, indent=2)
    path = f"{SCRIPT_DIR}/out/Tracker/exec_instr_tracker.json"
    with open(path, "w") as f:
        f.write(json_str)
    print(f"\n<Dumped `ExecInstrTracker` to `{path}`>")


def main():
    QUERIES_DIR = Path(f"{SCRIPT_DIR}/queries")

    # Iterate through all `.txt` files in the queries directory
    for query_file in QUERIES_DIR.glob("*.txt"):
        # Get the filename without `.txt` extension
        src_filename = query_file.stem

        print(f"Processing query file `{query_file.name}`")

        # Read file content
        with open(query_file, "r") as f:
            src = f.read()

        # Parse
        parser = ParserPG(src)
        try:
            parser.parse()
        except ParsingPGError as e:
            print(f"Error in `{query_file.name}`: {e}", file=stderr)
            continue

        # Plan generation
        plan_gen(parser, src_filename)
        plan_gen_o3(parser, src_filename)

    dump_exec_instr_tracker()


if __name__ == "__main__":
    main()
