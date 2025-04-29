from logging import getLogger
from typing import cast

import openai
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .types import LLMConfig, ScrapedData, SummarizedData

logger = getLogger(__name__)


class OutputText(BaseModel):
    """
    Defines the structure of the output result.
    """

    summarized_text: str = Field(..., description="Summarized text")


class Summarizer:
    """
    Class responsible for performing text summarization.
    """

    def __init__(self, config: LLMConfig):
        """
        Initializes the Summarizer with the given configuration.
        :param config: Configuration dictionary for the LLM.
        """
        self.config = config

    def _summarize(self, scraped_data: ScrapedData) -> str:
        """
        Summarizes the given scraped data.
        :param scraped_data: The data obtained from scraping.
        :return: The summarized text.
        """
        llm = ChatOpenAI(
            model=self.config["openai_model"],
            temperature=self.config["temperature"],
        )
        system_message = SystemMessage(
            content=str(
                self.config["prompt"].format(
                    language=self.config["language"],
                )
            )
        )
        human_message = HumanMessage(content=scraped_data["content"])
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        chain = prompt | llm.with_structured_output(OutputText)
        res = chain.invoke({})
        return cast(OutputText, res).summarized_text

    def run(self, scraped_data_list: ScrapedData) -> list[SummarizedData]:
        """
        Summarizes a list of scraped data and returns the results.
        :param scraped_data_list: List of scraped data.
        :return: List of summarized data with texts.
        """
        data: list[SummarizedData] = []
        for scraped_data in scraped_data_list:
            try:
                record: SummarizedData = {
                    **scraped_data,  # type:ignore
                    "summarized_text": self._summarize(scraped_data),
                }
                data.append(record)
            except openai.LengthFinishReasonError as e:
                logger.warning(f"Token limit exceeded. Skipping.\n{e}")
        return data
