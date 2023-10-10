# Functionality
- [x] Add pean slope property
- [ ] Add config validator
- [x] Add advanced filter manager
- [ ] Automated data file selection and sensible data file management
    - [ ] Use a specified data file or use the latest data file
- [x] Move from csv to sql and selective data load (sqlalchemy)
- [ ] Implement selective range generation using already generated data as a stepping stone


# Optimization
- [x] Add csv reader to skip redundant data generation
    - [x] Add validation of records

# BUGS AND ISSUES
- [x] Debug calculate_bb_distances - returns apparently incorrect number of distances
- [ ] Standardize stash_log_file and stash_graph_html if possible

# GENERATOR
- [x] generate backbone
- [x] process : calculate target (and partial path for unbound numbers)
- [x] generate full paths - run upwards even numbers, then odd numbers