import { motion } from "framer-motion";
import ClickSpark from "../components/ClickSpark";
import { useNavigate } from "react-router-dom";
import Button from "../components/Button";
import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AppleIntelligenceLoader = () => {
  const [isLoading, setIsLoading] = useState(true);
  const Navigate = useNavigate();
  const [pageContent, setPageContent] = useState<string>("");

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      if (!tabId) {
        console.log("No tab found");
        return;
      }
      chrome.tabs.sendMessage(
        tabId,
        { action: "extractPageContent" },
        (response) => {
          if (response && response.content) {
            setPageContent(response.content);
            setIsLoading(false);
          } else {
            console.log("No response from content script");
          }
        }
      );
    });
  }, []);

  return (
    <ClickSpark
      sparkColor='#fff'
      sparkSize={10}
      sparkRadius={15}
      sparkCount={8}
      duration={400}
    >
      <motion.div
        className="w-[420px] h-[500px] bg-yellow flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.9, ease: "ease" }
        }
      >


        <div className="relative w-[420px] h-[500px]">
          <div className="relative bg-white w-full h-full  top-0">
            <div className={`text-center space-y-4 absolute z-50 w-full h-full flex flex-col ${isLoading ? 'justify-center items-center' : 'justify-start items-start'}`}>
              {isLoading ? (<> <h2 className="text-4xl  text-black font-NanumMyeongjo">
                Summarizing...
              </h2>
                <p className="text-black max-w-xs">
                  Processing your request with advanced AI capabilities...
                </p>
              </>) : (
                <>
                  <div className="overflow-y-scroll h-[80%] mx-auto w-[95%] rounded-3xl">
                    <p className="text-black overflow-y-scroll">
                      <div className="text-left font-NanumMyeongjo p-6 rounded-2xl shadow-lg markdown-content">
                        
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            h1: ({ node, ...props }) => <h1 className="text-3xl lg:text-4xl font-extrabold mt-6 mb-4 text-black" style={{ fontSize: '2rem', minHeight: '15px' }} {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-2xl lg:text-3xl font-bold mt-6 mb-4 border-b pb-2 border-slate-200 text-black" style={{ fontSize: '1.5rem', minHeight: '15px' }} {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-xl lg:text-2xl font-semibold mt-5 mb-3 text-black" style={{ fontSize: '1.25rem', minHeight: '15px' }} {...props} />,

                            p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-5 mb-4 space-y-2 text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,
                            ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-5 mb-4 space-y-2 text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,
                            li: ({ node, ...props }) => <li className="mb-1 text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,

                            a: ({ node, ...props }) => <a className="text-black underline decoration-black/30 hover:decoration-black transition" target="_blank" rel="noopener noreferrer" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,

                            blockquote: ({ node, ...props }) => (
                              <blockquote className="border-l-4 border-black pl-4 italic text-black my-6 bg-gray-100 py-2 rounded-r-lg" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />
                            ),

                            code: ({ node, className, children, ...props }) => {
                              const isInline = !(className && /^language-/.test(className));
                              if (!isInline) {
                                return (
                                  <code className={`${className} text-sm font-mono text-black`} style={{ fontSize: '15px', minHeight: '15px' }} {...props}>
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <code className="bg-gray-200 rounded-md px-1.5 py-1 text-sm font-mono text-black" style={{ fontSize: '12px', minHeight: '15px' }} {...props}>
                                  {children}
                                </code>
                              );
                            },

                            pre: ({ node, ...props }) => (
                              <pre className="bg-gray-800 rounded-md p-4 my-6 overflow-x-auto" style={{ color: 'black', fontSize: '15px', minHeight: '15px' }} {...props} />
                            ),

                            strong: ({ node, ...props }) => <strong className="font-semibold text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,
                            em: ({ node, ...props }) => <em className="italic text-black" style={{ fontSize: '15px', minHeight: '15px' }} {...props} />,
                            hr: ({ node, ...props }) => <hr className="my-8 border-black" {...props} />,
                          }}
                        >
                          {pageContent}
                        </ReactMarkdown>
                      </div>
                    </p>
                  </div>
                </>
              )
              }
            </div>
            <div className="absolute bottom-5 p-4 z-[100000] w-full flex justify-center">
              <div className="mx-auto">
                <Button text={isLoading ? `CANCEL` : 'HOME'} handle={() => Navigate("/submit")} textColor="--primary-white" />
              </div>

            </div>
          </div>
          {(
            <div
              className="absolute inset-0 blur-xl opacity-90 animate-pulse "
              style={{
                background: 'linear-gradient(45deg, #8B5CF6, #EC4899, #F97316, #EAB308, #10B981, #3B82F6)',
                backgroundSize: '200% 200%',
                animation: 'gradientShift 3s ease-in-out infinite'
              }}
            />
          )}
        </div>
        <style>{`
        @keyframes gradientShift {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }
      `}</style>

      </motion.div>
    </ClickSpark>
  );
};

export default AppleIntelligenceLoader;