


model_description = """
**Sets**

- $I$: set of courses.

- $J$: set of years.

- $K$: set of groups.



**Parameters**

- $\mathrm{rating}_{i}$: rating of course $i$.

- $\mathrm{cfu}_{i}$: number of CFUs of course $i$.

- $\mathrm{semester}_{i}$: semester in which course $i$ is erogated.

- $\mathrm{minCFU}_{k}$: minimum number of CFUs for group $k$.

- $\mathrm{crosstab}_{ik}$: is $1$ if course $i$ belongs to group $k$, $0$ otherwise.



**Variables**

- $x_{ijk} \in [ 0,1]$: percentage of course $i$ in year $j$ in group $k$.

- $y_{i} \in \{0,1\}$: is $1$ if course $i$ is chosen, $0$ otherwise.

- $z_{ij} \in \{0,1\}$: is $1$ if course $i$ is chosen in year $j$, $0$ otherwise.



**Objective function**
$$
\max\sum\limits _{i,j,k} x_{ijk}\mathrm{\cdotp rating}_{i} \cdotp \mathrm{cfu}_{i}
$$


**Constraints**
$$
x_{ijk} =1,\\ \\ \\forall i\in \\{\\text{compulsory courses in year } j\\},\\forall k\in K,\\forall j\in J\\\\
\sum\limits _{i\in I,j\in J,k\in K} x_{ijk}\mathrm{\cdotp cfu}_{i} \leq \\text{CFU\_max\_tot}\\\\
\sum\limits _{i\in I\cap \\{\\text{sem. }1\\},k\in K} x_{ijk}\mathrm{\cdotp cfu}_{i} \leq \\text{CFU\_max\_sem},\\ \\ \\forall j\in J\\\\
\sum\limits _{i\in I\cap \\{\\text{sem. }2\\},k\in K} x_{ijk}\mathrm{\cdotp cfu}_{i} \leq \\text{CFU\_max\_sem},\\ \\ \\forall j\in J\\\\
\sum\limits _{k\in K} x_{ijk} \leq 1000\cdotp z_{ij},\\ \\ \\forall i\in I,\\forall j\in J\\\\
\sum\limits _{j\in J} z_{ij} \leq 1,\\ \\ \\forall i\in I\\\\
\sum\limits _{j\in J,k\in K} x_{ijk} \leq y_{i},\\ \\ \\forall i\in I\\\\
y_{i} \leq \sum\limits _{j\in J,k\in K} x_{ijk},\\ \\ \\forall i\in I\\\\
\sum\limits _{i\in I,j\in J} x_{ijk}\mathrm{\cdotp cfu}_{i} \geq \mathrm{minCFU}_{k},\\ \\ \\forall k\in K\\\\
\sum\limits _{j\in J} x_{ijk} \leq \mathrm{crosstab}_{ik},\\ \\ \\forall i\in I,\\forall k\in K
    
$$
"""

message_infeasible = "Problem is Infeasible. This usually means that you have either too many constraints (eg. CFUs per month is too low) or that you haven\'t chosen enough courses from both 1st and 2nd semester."
message_success = "Problem is Optimal! And the desired number of sub-optimal solutions has been computed."
disclaimer = "This is a student project not affiliated with Politecnico di Milano."
credits = 'Created by [Teo Bucci](https://github.com/teobucci)'+' '+'[Filippo Cipriani](https://github.com/SmearyTundra)'+' '+'[Marco Lucchini](https://github.com/marcolucchini)'