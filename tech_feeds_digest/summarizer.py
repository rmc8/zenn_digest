from typing import cast

from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .types import LLMConfig, ScrapedData, SummarizedData


class OutputText(BaseModel):
    summarized_text: str = Field(..., description="Summarized text")


class Summarizer:
    def __init__(self, config: LLMConfig):
        self.config = config

    def _summarize(self, scraped_data: ScrapedData) -> str:
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
        data: list[SummarizedData] = []
        for scraped_data in scraped_data_list:
            record: SummarizedData = {
                **scraped_data,  # type:ignore
                "summarized_text": self._summarize(scraped_data),
            }
            data.append(record)
        return data
