# BGLappTrials
 
The algorithm, in its current state, focuses on provide the most optimum route to effectively cater to indent requirements of daughter stations. It prioritises stations with higher average sales. 
The user is required to input the indent quantity filed by daughter stations, followed by available LCV IDs and their coordinates. The code cross-checks with the LCV database to determine their capacities.
Once inputs are received, the data is processed. Initially, the distance between LCVs and loading stations is determined using Haversine formula (straight-line distance). This enables the program to allot LCVs to their closest filling stations. 
Next, the program calculates the optimum route and creates maps between the starting point, loading station and daughter station. Following this, the loading time is calculated, based on the loading rates at the specific stations and capacities of LCVs. 
Now, if a large number of LCVs are allotted to the same loading station, the program is also capable of determining whether the time taken to fill LCVs (considering currently loading LCVs) is more or less than travel time to the next closest loading station. The LCVs are either instructed to wait at the current station or can be told to move to the next closest loading station, depending on which time is lesser. 
 
***
