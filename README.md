## API Structure
| - ENDPOINTURL
|   | - {user_id}
|   |   | - get_user_name
|   |   |   | - **get_user_name_lambda**
|   |   | - get_user_cards
|   |   |   | - {base_language_id}
|   |   |   |   | - {target_language_id}
|   |   |   |   |   | - **get_user_cards_lambda**
|   |   | - post_user
|   |   |   | - {user_name}
|   |   |   |   | - **post_user_lambda**
|   |   | - post_card
|   |   |   | - {base_language_id}
|   |   |   |   | - {target_language_id}
|   |   |   |   |   | - {card_id}
|   |   |   |   |   |   | - {card_detail}
|   |   |   |   |   |   |   | - **post_card_lambda**
|   |   | - delete_card
|   |   |   | - {base_language_id}
|   |   |   |   | - {target_language_id}
|   |   |   |   |   | - {card_id}
|   |   |   |   |   |   | - **delete_card_lambda**
|   |   | - en2jp
|   |   |   | - card
|   |   |   |   | - {word}
|   |   |   |   |   | - **get_en2jp_card_word**
|   |   |   |   |   | - sentence
|   |   |   |   |   |   | - **get_en2jp_card_sentence_lambda**
|   |   |   |   |   | - comment
|   |   |   |   |   |   | - **get_en2jp_card_comment_lambda**
|   |   |   | - story
|   |   |   |   | - {word_diff}
|   |   |   |   |   | - {content_diff}
|   |   |   |   |   |   | - {grammar_diff}
|   |   |   |   |   |   |   | - {story_context}
|   |   |   |   |   |   |   |   | - **get_en2jp_story_lambda**
|   |   | - jp2en