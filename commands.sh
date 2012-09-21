export BASIC_COMMAND="PYTHONPATH=''; ./infer_issue_adjustments.py \
		--vote_chambers_file=votes_with_chamber.csv \
		--mult_filename=v12.2-train-mult.dat_all \
		--gammas_filename=v12.2-labeled_topics-train-all/final.gamma "

export OUTPUT_ROOT="results"
mkdir -p ${OUTPUT_ROOT}

# Fit the issue-adjusted model with different values of lambda.
session=109
for chamber in s h; do
    for weight in 0.0001 0.001 0.01 0.1 1.0 10.0 100.0 1000.0; do
	for model in globalzero ideal; do
	    OUTPUT_DIR=${OUTPUT_ROOT}/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_variational_${model}/${session}/${weight};
	    for subset in 0 1 2 3 4 5; do
		mkdir -p ${OUTPUT_DIR}
		CMD="${BASIC_COMMAND} \
	          --subset=${subset} \
                  --model=globalzero \
    	          --session=${session} \
                  --output_root=${OUTPUT_DIR} \
		  --votes_filename=v12.2-train-votes-disjoint-docs.dat_${subset} \
		  --votes_validate_filename=v12.2-validate-votes-disjoint-docs.dat_${subset} \
		  --chamber=${chamber} \
		  --regularization_weight=${weight};"
	    echo ${CMD}
	    ${CMD}
	    done
	done
    done
done

# Fit the issue-adjusted and ideal point models to ALL votes/bills.
session=111
weight=1.0
for subset in all; do
    for chamber in h s; do
        for model in globalzero ideal; do
	    OUTPUT_DIR=${OUTPUT_ROOT}/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_variational_${model}/${session}/${weight};
	    mkdir -p ${OUTPUT_DIR}
	    CMD="${BASIC_COMMAND} \
		--subset=${subset} \
                --model=${model} \
		--session=${session} \
		--output_root=${OUTPUT_DIR} \
		--votes_filename=v12.2-train-votes-disjoint-docs.dat_${subset} \
		--chamber=${chamber} \
		--regularization_weight=${weight};"
	    echo ${CMD}
	    ${CMD}
	done
    done
done

# Note that we do not include the original permutation-test files.
# This is because we shuffled the data and ran the above commands on
# the shuffled data.

# Fit the issue-adjusted model (globalzero) and the ideal point model
# (ideal) with weight=1 for different sessions.
export weight=1.0
for session in 106 107 108 109 110 111; do
    for subset in 0 1 2 3 4 5; do
	for model in globalzero ideal; do
	    OUTPUT_DIR=${OUTPUT_ROOT}/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_variational_${model}/${session}/${weight};
	    for chamber in s h; do
		mkdir -p ${OUTPUT_DIR}
		CMD="${BASIC_COMMAND} \
		    --subset=${subset} \
                    --model=${model} \
		    --session=${session} \
		    --output_root=${OUTPUT_DIR} \
		    --votes_filename=v12.2-train-votes-disjoint-docs.dat_${subset} \
		    --votes_validate_filename=v12.2-validate-votes-disjoint-docs.dat_${subset} \
		    --chamber=${chamber} \
		    --regularization_weight=${weight};"
		echo ${CMD}
		${CMD}
	    done
	done
    done
done

# Fit the issue-adjusted model when topics were fit with traditional
# lda (and not labeled topics).
for session in 106 107 108 109 110 111; do
    for weight in 1.0; do
	for subset in 0 1 2 3 4 5; do
	    for chamber in s h; do
		for model in globalzero ideal; do
		    OUTPUT_DIR=${OUTPUT_ROOT}/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_variational_${model}_vanillalda/${session}/${weight};
		    mkdir -p ${OUTPUT_DIR
			CMD="PYTHONPATH=''; ./infer_issue_adjustments.py \
		--subset=${subset} \
		--session=${session} \
		--vote_chambers_file=votes_with_chamber.csv \
		--mult_filename=v12.2-train-mult.dat_all \
                --model=globalzero \
                --output_root=${OUTPUT_DIR} \
                --gammas_filename=v12.2-vanilla_lda_alpha_1byk-train-${subset}/final.gamma \
                --votes_filename=v12.2-train-votes-disjoint-docs.dat_${subset} \
		--votes_validate_filename=v12.2-validate-votes-disjoint-docs.dat_${subset} \
		--chamber=${chamber} \
		--regularization_weight=${weight} \
		echo ${CMD}
		${CMD}
	    done
	done
    done
done


# Fit a traditional ideal point model across sessions.
for session in 106 107 108 109 110 111; do
    for weight in 1.0; do
	OUTPUT_DIR=${OUTPUT_ROOT}/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_variational_globalzero_vanillalda/${session}/${weight};
	for subset in 0 1 2 3 4 5; do
	    for chamber in s h; do
		mkdir -p ${OUTPUT_DIR}
		CMD="PYTHONPATH=''; ./infer_issue_adjustments.py \
		--subset=${subset} \
		--session=${session} \
		--vote_chambers_file=votes_with_chamber.csv \
		--mult_filename=v12.2-train-mult.dat_all \
                --model=globalzero \
                --output_root=${OUTPUT_DIR} \
                --gammas_filename=v12.2-vanilla_lda_alpha_1byk-train-${subset}/final.gamma \
                --votes_filename=v12.2-train-votes-disjoint-docs.dat_${subset} \
		--votes_validate_filename=v12.2-validate-votes-disjoint-docs.dat_${subset} \
		--chamber=${chamber} \
		--regularization_weight=${weight}"
		echo ${CMD}
		${CMD}
	    done
	done
    done
done
