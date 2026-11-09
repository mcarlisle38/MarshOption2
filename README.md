# MarshOption2

Assumptions made (these would need to be clarified with customer in real world (IRL)):

	User Functionality
		No text inputs required from the user, the user simply drops the input files into the home directory and executes application
		Output file is dropped in same directory
		User will only encounter any text feedback when they encounter an error which will be displayed on console
		There will only be one output file at any given time for simplicity
			- If a previous output file already exists in the home directory then it will be overwritten
		The 3 example files with 17 transactions across 3 files is a 'normal' load and the application will handle this load
			- IRL we should define what the maximum load the system would need to handle and in what time frame for design
		
	Inputs
		All input files will need to be dropped in the home directory of the project
		User can input as many CSV, JSON or XML files as they want 
		CSV file will be comma delimited (other delimiters not accepted), header is defined as non-case sensitive
		JSON will be in valid json format within transactions object, keys will be non-case sensitive
		XML will be in valid XML format within transactions object, element names will be non-case sensitive
		
	Output
		Output will be in SQLite format
		Output file will be named 'output_dataset'
		Output file will be dropped in the home directory
		Output file will overwrite any existing files with the same filename
		Fields will be listed as lower case and named:
			transaction_uti
			isin
			notional
			notional_currency
			eur_notional - will be same value format as notional input, range 0 - 99999999.0
			transaction_type
			transaction_datetime
			exchange_rate
			legal_entity_identifier
		The eur_notional field will be calculated by notional rate * exchange rate

	Data Types
		transaction_uti: upper case alphanumeric, max 45 characters - IRL further clarification would be required on format verification e.g. 'TRANSCATIONID' string in centre
		isin: alphanumeric, max 12 characters - IRL further clarification would be required on format e.g. 2 letter country code, 9 character NSIN, check digit
		notional: numeric, max 1 decimal place, range 0 - 99999999.0, must be able to handle E notation values
		notional_currency: 3 character alphabetic, non-case sensitive
		transaction_type: Buy or sell the only valid inputs, non-case sensitive
		transaction_datetime: date time format, accuracy only down to the seconds (no ms), must take into account timezone offsets
		exchange_rate: numeric type, must be accurate to 10 decimal places, calculations would ideally be performed using fixed point numeric type
		legal_entity_identifier: uppercase alphanumeric, max 20 characters
		
	Functionality
		Data integration will be performed in memory
			- To make this scale to larger data sets data may need to be stored in storage or durable persistence
		There will be no validation on max number of records accepted to be processed
		There will be no streaming of input elements being picked up from input files
			- This would be a possibility for larger datasets if required for further enhancements
		This process will be a singleton so it is assumed there will be no writing thread contention on the output file
		The process will require to check for write contention on the input files in case users have the input files open on their machine
		There will be no multi-threading for files to be processed in parallel to enhance processing performance