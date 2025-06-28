import { RiArrowRightUpLine } from "react-icons/ri";
import { MdDelete } from "react-icons/md";
import { MdOutlineEditNote } from "react-icons/md";

interface CardProps {
    title: string;
    description: string;
    bgColor: string;
    onClick: () => void;
    isSelected: boolean;
    RedirectUrl?:string;
    date:string
    confirmDelete:boolean;
    setDeleteClicked:(vale: boolean) => void;
    isSearchAll:boolean;
    type:string;
    activeTab:string;
}



export default function Cards({ title, description, bgColor,onClick,isSelected,RedirectUrl,date,confirmDelete,setDeleteClicked,
type,
activeTab,
isSearchAll

 }: CardProps) {
  console.log("The type is:", type);

    return (
        <>
          <div
            className={`${bgColor} rounded-lg p-4 mb-4 relative cursor-pointer flex-col justify-between overflow-hidden
            ${
              isSelected
                ? `scale-100 ${(description.length>316?'h-full':'h-[415px]')} w-[100%]`
                : 'scale-100 h-[130px] hover:scale-[1.02]'
            } transition-all duration-500 ease-in-out will-change-transform
            
            
            `}
            onClick={onClick}
            style={{
              backgroundColor: `var(${bgColor})`,
              ...(!isSearchAll && (type !== activeTab && activeTab !== "All")  ? { display: 'none' } : {})
            }}
            
          >
            <div className="flex justify-between items-start overflow-hidden">
           {isSelected && type !== "Note" ? 
           
           <button 
                   disabled={confirmDelete}
                   className='p-0 flex-shrink-0'>
                     <MdDelete
                     onClick={()=>setDeleteClicked(true)}
                     size={24} className="self-start"/>
              </button>

           
           :null}
              <div className={`flex-1 min-w-0 ${isSelected ? 'p-14 pt-28 pr-8' : 'pr-8'}`}>
                {isSelected ? (
                  <p className="nyr text-[16px] mb-2 truncate">{date}</p>
                ) : null}
                <h2 className={`text-[22px] nyr mb-[0.8rem] leading-tight ${
                  isSelected 
                    ? 'break-words' 
                    : 'truncate'
                }`}>
                  {isSelected
                    ? title
                    : title}
                </h2>
                <p className={`font-SansMono400 text-sm leading-snug opacity-90 ${
                  isSelected 
                    ? 'pb-[45px] break-words' 
                    : 'line-clamp-2'
                }`}>
                  {description}
                </p>
              </div>
             <div className="flex-shrink-0 w-[10%] min-w-[40px] flex flex-col justify-start items-end">
             <div className="w-full flex justify-end mb-2">
                {
                  RedirectUrl ?
                  <RiArrowRightUpLine size={28} className="cursor-pointer" onClick={()=>{isSelected?window.open(RedirectUrl):null}}/>
                  :
                  <MdOutlineEditNote size={28} className="cursor-pointer" onClick={()=>{isSelected?window.open(RedirectUrl):null}}/>
                }
              </div>
              {isSelected && type !== "Note" && RedirectUrl && (
                <div className="w-full flex justify-end">
                  <p className="font-SansMono400 text-[10px] mt-1 truncate max-w-full text-right">
                    {RedirectUrl.split("//")[1]?.split("/")[0] || RedirectUrl}
                  </p>
                </div>
              )}
             </div>
            </div>
          </div>
        </>
      );
      
      
}