
package template;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.annotation.processing.SupportedAnnotationTypes;
import javax.xml.bind.annotation.XmlRootElement;

/**
 * Element-value pairs
 */
@SupportedAnnotationTypes(value = { "foo" })
@XmlRootElement(name = "foo", namespace = "bar")
public class LineWrapping {

    class Example {}

    /**
     * 'extends' clause
     */
    class ExampleExtends extends Example {}

    interface I1 {}

    interface I2 {}

    interface I3 {}

    /**
     * 'implements' clause
     */
    class ExampleImplements implements I1, I2, I3 {}

    /**
     * Parameters
     */
    class ExampleParameters {

        ExampleParameters(int arg1, int arg2, int arg3, int arg4, int arg5, int arg6) {
            this();
        }

        ExampleParameters() {}
    }

    class FirstException extends Exception {}

    class SecondException extends Exception {}

    class ThirdException extends Exception {}

    static class OtherStatic {

        public static void doSomething() {}

        public static void bar(int i, Object nested) {
            // TODO Auto-generated method stub

        }
    }

    /**
     * 'throws' clause
     */
    class ExampleThrow {

        ExampleThrow() throws FirstException, SecondException, ThirdException {
            OtherStatic.doSomething();
        }

        public ExampleThrow(int i, int j, int k, int l, int m, int n, int o) {}

        class ExampleSubSub {}
    }

    /**
     * Declaration
     */
    class ExampleDeclaration {

        public final synchronized java.lang.String a_method_with_a_long_name() {
            return "foo";
        }
    }

    /**
     * Parameters
     */
    class ExampleParameters2 {

        void foo(int arg1, int arg2, int arg3, int arg4, int arg5, int arg6) {}
    }

    /**
     * 'throws' clause
     */
    class ExampleThrow2 {

        int foo() throws FirstException, SecondException, ThirdException {
            OtherStatic.doSomething();
            return 1;
        }
    }

    /**
     * Constants
     */
    enum ExampleConstant {
        CANCELLED,
        RUNNING,
        WAITING,
        FINISHED
    }

    enum ExampleColor {
        GREEN(0, 255, 0),
        RED(255, 0, 0);

        ExampleColor(int r, int g, int b) {

        }
    }

    /**
     * 'implements' clause
     */
    enum ExampleEnumImplements implements I1, I2, I3 {}

    void foo() {
        OtherStatic.bar(100, nested(200, 300, 400, 500, 600, 700, 800, 900));
    }

    private Object nested(int i, int j, int k, int l, int m, int n, int o, int p) {
        return null;
    }

    /**
     * Qualified invocations
     */
    int foo(String a) {
        return a.length();
    }

    /**
     * Explicit constructor invocations
     */
    class ExampleConstructor extends ExampleThrow {

        ExampleConstructor() {
            super(100, 200, 300, 400, 500, 600, 700);
        }

        /**
         * Object allocation arguments
         */
        ExampleThrow fooAllocation() {
            return new ExampleThrow(100, 200, 300, 400, 500, 600, 700);
        }

        int foo2() {
            int sum = 100 + 200 + 300 + 400 + 500 + 600 + 700 + 800;
            int product = 1 * 2 * 3 * 4 * 5 * 6 * 7 * 8 * 9 * 10;
            boolean val = true && false && true && false && true;
            return product / sum;
        }

        int foo(boolean argument) {
            return argument ? 100000 : 200000;
        }

        /**
         * Array initializers
         */

        int[] fArray = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 };

        /**
         * Assignments
         */

        private static final String string = "TextTextText";

        void foo3() {
            for (int i = 0; i < 10; i++) {}
            String s;
            s = "TextTextText";
        }

        /**
         * 'for'
         */

        void foo(int argument) {
            for (int counter = 0; counter < argument; counter++) {}
        }

        /**
         * Compact 'if else'
         */

        int fooIfElse(int argument) {
            if (argument == 0) {
                return 0;
            }
            if (argument == 1) {
                return 42;
            } else {
                return 43;
            }
        }

        /**
         * 'try-with-resources'
         *
         * @throws IOException
         * @throws FileNotFoundException
         */

        void fooTry() throws FileNotFoundException, IOException {
            try (FileReader reader1 = new FileReader("file1"); FileReader reader2 = new FileReader("file2")) {}
        }

        /**
         * 'multi-catch'
         */
        void foo() {
            try {} catch (IllegalArgumentException | NullPointerException | ClassCastException e) {
                e.printStackTrace();
            }
        }

        /**
         * Type references
         */
        Map<String, ? extends java.lang.Object> map = new HashMap<String, java.lang.Object>();

        /**
         * Type parameters
         */
        class Example<S, T extends String & List, U> {}

    }

}