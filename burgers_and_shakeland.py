import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("burgers_and_shakeland.csv")

# Cleaning necessary?
# Testing for duplicates
# All values make sense as possible though and aren't clearly presented such that duplicates would be easy to identify if they existed

duplicate_check = pd.DataFrame(df.groupby(["DateTime","Location","Transaction EmployeeID","ItemID"]).count())

duplicate_check[~duplicate_check.duplicated()]

# Does Employee Name and Transaction EmployeeID always coincide?
# Does Item and ItemID always coincide?
df[["Employee Name", "Transaction EmployeeID"]].drop_duplicates()
df[["Item", "ItemID"]].drop_duplicates()

# Different locations for the same employee
df[["Employee Name","Location"]].drop_duplicates()
fancy_pants = df[df["Transaction EmployeeID"] == 110][["Employee Name","DateTime","Location"]].drop_duplicates()

both_locations = fancy_pants[fancy_pants["Location"] == "State Street"].join(fancy_pants[fancy_pants["Location"] == "Union Heights"].set_index("DateTime"),on="DateTime",rsuffix="_union")

both_locations[~both_locations["Location_union"].isna()]


# Which location is the busiest? Does the answer to this question change throughout the day?
df['DateTime'] = pd.to_datetime(df['DateTime'])

df["Date"] = df["DateTime"].dt.date
df["Time"] = df["DateTime"].dt.time 

df.groupby(["Location"]).count()

# State Street has more items sold in general (but did it open first, etc.)

df.groupby(["Location"]).min()

# Nope, they opened on the same day

# Let's test for if one has any sales for a day missing for the other one
by_date = df.groupby(["Date","Location"]).count()[["DateTime"]]

compared_dates = pd.pivot_table(by_date, values ="DateTime", index=["Date"], columns = "Location").reset_index()

compared_dates.loc[(compared_dates["State Street"] == 0) | (compared_dates["Union Heights"] == 0)]

# Great that's not a complication to the considerations

# Now focusing on time
by_time = df.groupby(["Time","Location"]).count()[["DateTime"]]

compared_times = pd.pivot_table(by_time, values = 'DateTime', index=['Time'], columns = 'Location').reset_index()

plt.plot(compared_times["Time"], compared_times["State Street"], label="State Street")
plt.plot(compared_times["Time"], compared_times["Union Heights"], label="Union Heights")
plt.xticks([])
plt.legend()
plt.show()

# It varies by time let's see the specifics
compared_times["isStateStreetBusier"] = compared_times.apply(lambda row: row["State Street"] > row["Union Heights"],axis=1)

compared_times[compared_times["isStateStreetBusier"] == True]

# from 11:00 to 13:30 and 16:30 to 21:00
# let's show that in a more pretty way:

plt.plot(compared_times["Time"], compared_times["State Street"], label="State Street")
plt.plot(compared_times["Time"], compared_times["Union Heights"], label="Union Heights")
plt.xticks([20,30,42,60])
plt.legend()
plt.savefig("business_by_time_and_location.png")






# Which three (3) employees had the highest percent increase to their monthly sales from March to April? What were their percent increases?
df["Month"] = df["DateTime"].dt.month_name()
by_month_and_employee = df[["Transaction EmployeeID","Month","Price"]].groupby(["Transaction EmployeeID","Month"]).sum()
compared_months = pd.pivot_table(by_month_and_employee,values="Price",index=["Transaction EmployeeID"],columns="Month")

percent_increases = pd.DataFrame(compared_months.apply(lambda row: row["April"]/row["March"],axis=1))

percent_increases.sort_values([0],ascending=False)

#110 with a 60.4125% increase, 111 with a 4.1383% increase, 102 with a 0.4524% increase




# A combo meal consists of 1 Burger, 1 Fry, and either a Drink or a Shake. How many combo meals were sold from the State Street location in April?
# Assuming that every DateTime and EmployeeID represents a single order (which could be an odd assumption in that only 1 order is placed every 15 minutes every time this way...) we would get the following:
possible_combo_meals = df.loc[(df["Location"] == "State Street") & (df["DateTime"].dt.month == 4)][["DateTime", "Location", "Transaction EmployeeID", "ItemID"]].groupby(["DateTime","Location", "Transaction EmployeeID"]).agg(list)

def get_minimum_item_count(possible_order):
    """ Get the minimum combo item count between the 1s, 2s, and 3 or 4s
    input:
    output:
    """
    counts = {}
    for item in possible_order:
        counts[item] = counts.get(item, 0) + 1
    counts["3 or 4"] = counts.get(3,0) + counts.get(4,0)
    return min(counts.get(1,0),counts.get(2,0),counts.get("3 or 4"))
    
sum(possible_combo_meals["ItemID"].apply(get_minimum_item_count))

# possible_combo_meals["possible_combo_meals"] = possible_combo_meals["ItemID"].apply(get_minimum_item_count)


# 99