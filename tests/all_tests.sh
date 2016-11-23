testdir=$(dirname "$(readlink -f $0)")
errcount=0

col_good="\033[0;32m"  # green
col_bad="\033[0;31m"   # red
col_off="\033[0m"      # no color

echo "***  Running all tests for ChatExchange  ***"
echo
echo "Interpreter:      $(python --version) ( $(which python) )"
echo "Test directory:   $testdir"
echo

for x in "$testdir"/test_*.py ; do
	basename "$x"

	if PYTHONPATH="$(pwd)" python "$x" ; then
		echo -e "${col_good}  --> ok${col_off}"
	else
		echo -e "${col_bad}  --> FAILED !!!${col_off}"
		errcount=$(( $errcount+1 ))
	fi
done

echo
if test $errcount -eq 0 ; then
	echo -e "${col_good}Finished successfully.${col_off}"
else
	echo -e "${col_bad}Exited with $errcount errors.${col_off}"
fi


