/**
 * Blank Lines
 */

package template;

import java.util.LinkedList;

public class BlankLines {

    public class Another {}

    public static class Example {

        public static class Pair {

            public String first;
            public String second;
            // Between here...

            // ...and here are 10 blank lines
        }

        private LinkedList fList;
        public int counter;

        public Example(LinkedList list) {
            fList = list;
            counter = 0;
        }

        public void push(Pair p) {
            fList.add(p);
            ++counter;
        }

        public Object pop() {
            --counter;
            return fList.getLast();
        }
    }

}