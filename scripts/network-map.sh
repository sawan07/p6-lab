#!/bin/sh
# Shows which containers sit in which network tier and proves the isolation (report 1.3.1).
echo "NETWORK TIERS (lab stand-in for the VPC subnets)"
for n in edge private data; do
  net="p6-lab_$n"
  internal=$(docker network inspect -f '{{.Internal}}' "$net")
  members=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$net" | tr ' ' '\n' | sed 's/^p6-lab-//; s/-[0-9]*$//' | sort -u | tr '\n' ' ')
  printf "  %-8s internal=%-5s  %s\n" "$n" "$internal" "$members"
done
echo
echo "REACHABILITY TESTS"
t() { if docker compose exec -T "$1" sh -c "$3" >/dev/null 2>&1; then r=ALLOWED; else r=BLOCKED; fi; printf "  %-14s -> %-22s %s (expected %s)\n" "$1" "$2" "$r" "$4"; }
t gateway       "read-service:8000"   "wget -qO- -T2 http://read-service:8000/read/config"            ALLOWED
t gateway       "db-primary:5432"     "nc -z -w2 db-primary 5432"                                   BLOCKED
t gateway       "redis:6379"          "nc -z -w2 redis 6379"                                        BLOCKED
t read-service  "read-replica:5432"   "python -c \"import socket;socket.create_connection(('read-replica',5432),2)\"" ALLOWED
t read-service  "internet (pypi.org)" "python -c \"import socket;socket.create_connection(('pypi.org',443),3)\""     BLOCKED
