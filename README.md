# MovieLens recommender system
This repository contains a recommender system which work on a [small subset of MovieLense dataset](https://github.com/lukkiddd-tdg/movielens-small).
## Taking a look at data
You can see data exploration jupyter notebook in notebook directory.

In the full dataset, there are 27,278 movies and 138,493 users in dataset. Each user has rated at least 20 movies same as this dataset.

<u>I will only use rating and movie data, but not the tags and links.</u>
## Personalized recommender
This recommender goals is to predict rating that a user would give to movies that they have not watched, and then recommend top-N highest rating to the user.

<u>Because the number of users in movie rating website can be multiple times more than the number of movies</u>, **I will use item-based collaborative filtering recommender** so that the computation is substantially lower than user-based collaborative filtering.

The following is the steps to build rudimentary item-based recommender system.
### 1. Calculate similarity between movies
Similarity matrix between all movies will be used to calculate rating for movie that a user haven't watched it later.

The measurement for similarity in this matrix is cosine similarity. Given movie A and B, the cosine similarity between them is calculated as:

$$\cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|} = \frac{\sum_{u=1}^{U} A_u B_u}{\sqrt{\sum_{u=1}^{U} A_u^2} \sqrt{\sum_{u=1}^{U} B_u^2}}$$

Where $U$ is the set of users who rated both movie A and B, and $A_u$ and $B_u$ in above equation are actually **normalized rating** a user $u$ gave to both movies.
The following is the example of similarity matrix.

<table>
  <tr>
    <th></th>
    <th>A</th>
    <th>B</th>
  </tr>
  <tr>
    <th>A</th>
    <td>1</td>
    <td>0.8</td>
  </tr>
  <tr>
    <th>B</th>
    <td>0.4</td>
    <td>1</td>
  </tr>
</table>

<u>This matrix is pre-calculated before serving recommendation</u>, so it can be run as batch processing job.

### 2. Finding movies similar to movies a given user has watched
During serving recommendation to a user, firstly, one needs to find the movies similar to the movies the user has watched.

I use movie similarity matrix to find that. I consider the movie to be similar to another movie if the cosine similarity is more than threshold.

I also sort the results based on similarity in descending order, and select the top N similarity that I will consider.

<u>This step and next step onward, are done during serving recommendation.</u>
### 3. Predicting rating for similar movies
Now, I have the following data
- A set of movies similar to one of the movie the user has watched.
- A set of movie's ratings that the user gave.

For a candidate movie to recommend $m$, one can predict the rating the user would give to $m$ as describe in the following equation.

$$ R(m) = \frac{\sum_{w=1}^{W} sim(w, m) * r_w }{\sum_{w=1}^{W} sim(w, m)} $$

where $W$ is a set of movies that the user has watched and similar to a candidate movie. $r$ is normalized rating.

### 4. Return recommended movies
After getting predicted rating for all candidate movies, I sort it based on predicted rating descending order, and return top N movies as recommended results.

## Evaluating the recommender system
There are many ways to evaluate recommender system. One way is to find the error between the predicted rating of a movie and the actual rating the the user gave.

One can use `python -m tools.evaluate_user_recommendation --user-id <user id>` to find the MSE of specified user.

Please note that all data in the dataset is used to train the similarity matrix, so this isn't a fair evaluation and for demonstration purpose only.

## Implementation detail
- Data is required to be seed to database before serving REST API. Seeding including insert 
- I chose to save similarity matrix in SQLite, and query only the relevant records during serving recommendation for memory efficiency.

## Running the REST API server

## How to play with API
Open browser and go to `http://localhost:8000/docs` to use interactive API docs (from swagger UI).
In this page you can select API that you want to test, enter user ID and get the recommended movies.

## How to improve the recommender system
- When a user just start using the system, there isn't enough movie watching history to predict the rating of the movie to recommend to them. One can use non-personalized recommender system to recooomend e.g. recommmend popular movie recently. The system become hybrid recommender system.
- One can decide the method to do the evaluation and use it for regression test i.e. test after building recommender whether the recommnedation quality regress or not.
- In order to fairly evaluate the recommender system, in my opinion, one should use A/B testing between 2 recommender systems and see how the user respond to the recommendation.