.DEFAULT_GOAL := ci

# Export values directly so shell metacharacters remain data for validation.
export AI OUT REGEN_ROOT SHA HF_LAYOUT_FORK HF_LAYOUT_UPSTREAM HF_LAYOUT_MIRROR
export BUMP TEST K PYTHON_VERSION HF_LAYOUT_ADAPTER

.PHONY: %
%:
	@just $@
