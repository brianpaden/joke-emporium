# Joke Dataset Data Sources

## Primary GitHub Repositories

### Large-Scale Datasets

1. **taivop/joke-dataset** - 200k English jokes
   - URL: https://github.com/taivop/joke-dataset
   - Format: JSON
   - Features: Multiple sources (Reddit, stupidstuff.org, wocka.com)
   - Has categorization (e.g., "One Liners")
   - Well-structured with body field and metadata

2. **orionw/rJokesData** - 550k+ rated jokes
   - URL: https://github.com/orionw/rJokesData
   - Format: TSV
   - Features: User ratings, temporal data (11 years of r/Jokes)
   - Research paper: "The r/Jokes Dataset: a Large Scale Humor Collection" (LREC'20)
   - Good for understanding joke quality metrics

3. **amoudgl/short-jokes-dataset** - 231k short jokes
   - URL: https://github.com/amoudgl/short-jokes-dataset
   - Format: CSV/JSON
   - Features: Scraped from multiple websites
   - Good for: Short-form jokes (10-200 characters)
   - Includes reddit-cleanjokes.csv subset

### Smaller/Specialized Datasets

4. **kylecs/jokes-dataset-json** - ~1k jokes
   - URL: https://github.com/kylecs/jokes-dataset-json
   - Format: JSON
   - Features: Setup/punchline structure, maturity ratings, Reddit scores
   - Good for: Understanding two-part joke structure

5. **shuttie/dadjokes** (Hugging Face)
   - URL: https://huggingface.co/datasets/shuttie/dadjokes
   - Features: Curated dad jokes with 5+ votes
   - Source: Kaggle Reddit Dad Jokes

6. **Fraser/short-jokes** (Hugging Face)
   - URL: https://huggingface.co/datasets/Fraser/short-jokes
   - Format: CSV
   - Size: 231,657 jokes

## Research Datasets

7. **Jester Datasets**
   - URL: https://eigentaste.berkeley.edu/dataset/
   - Features: Jokes with user ratings (collaborative filtering research)
   - Good for: Understanding joke preferences

8. **Naughtyformer Dataset** - 92k jokes
   - Categories: Clean, Dark, Dirty
   - Good for: Maturity-based categorization

9. **CleanComedy** - 44k English + 40k Russian jokes
   - Features: Toxicity-filtered corpus
   - Good for: Family-friendly content

## Academic Resources

10. **"Is This A Joke?" Dataset**
    - URL: https://www.researchgate.net/publication/337531111_Is_This_A_Joke_A_Large_Humor_Classification_Dataset
    - Good for: Humor classification methodology

11. **Knowledge Amalgam** - 96k jokes
    - Sources: CrowdTruth and Subreddits
    - Features: Deduplicated

## Categorization & Taxonomy References

12. **Cognitive Jokes Taxonomy**
    - URL: https://consc.net/notes/humor.html
    - Types: Interpretational jokes (SDS, DSS, SDD, SD, DS)
    - Good for: Understanding joke structure theory

## Potential APIs to Explore

- icanhazdadjoke.com API
- Official Joke API
- JokeAPI.dev
- Chuck Norris API (for specific category)
- HumorAPI - filtering by type, blacklist flags, and ratings
- API Ninjas Jokes - lightweight REST API with topic filters
- Jokes One API - categorized jokes and joke-of-the-day endpoints
- DadSoFunny API - dad-joke corpus with general/programming/knock-knock filters

## Scraping Targets (with permission/robots.txt compliance)

- r/Jokes (via Reddit API)
- r/dadjokes
- r/puns
- r/cleanjokes
- stupidstuff.org
- wocka.com

## Categorization Strategies from Research

Based on the datasets above, common categorization dimensions include:

1. **By Structure**: One-liners, setup/punchline, stories
2. **By Content**: Puns, wordplay, observational, dark, clean, dad jokes
3. **By Maturity**: Clean, PG-13, Adult, Dark
4. **By Cognitive Type**: Interpretational, situational, linguistic
5. **By Topic**: Technology, animals, food, relationships, work, etc.
6. **By Quality**: User ratings, upvotes, engagement metrics
7. **By Length**: Short (<50 chars), medium, long

## Notes for Implementation

- Python 3.10+ with Pydantic for data models
- JSON as primary format
- Consider multi-label categorization (jokes can fit multiple categories)
- Include metadata: source, rating, date, author (if available)
- Plan for deduplication across sources
